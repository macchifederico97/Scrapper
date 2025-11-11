using System.Text.Json;
using System.Text;
using System.Timers;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using System.Text.Json.Nodes;
using System.Runtime.InteropServices;

namespace BatchOrchestrator.Services
{

    public class BatchScheduler : BackgroundService
    {
        private readonly ILogger<BatchScheduler> _logger;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly string _configPath = "data/batch_config.json";
        private readonly string _logPath = "data/batch_log.json";
        private readonly string _responsePath = "data/batch_response.json";
        private static readonly SemaphoreSlim _fileLock = new SemaphoreSlim(1, 1);
        private readonly BatchReportMailer _mailer;
        private DateTime _lastEmailSent = DateTime.MinValue;
        private readonly BatchResponseRepository _responseRepo;
        private static readonly SemaphoreSlim _fileLock2 = new(1, 1);

        public BatchScheduler(ILogger<BatchScheduler> logger, IHttpClientFactory httpClientFactory, BatchReportMailer mailer, BatchResponseRepository responseRepo)
        {
            _logger = logger;
            _httpClientFactory = httpClientFactory;
            _mailer = mailer;
            _responseRepo = responseRepo;
        }


        public class BatchConfig
        {
            public string Id { get; set; }
            public string Endpoint { get; set; }
            public Dictionary<string, string> Params { get; set; }
            public string Time { get; set; }
            public bool Active { get; set; }
        }


        protected override async Task ExecuteAsync(CancellationToken stoppingToken)
        {
            _logger.LogInformation("Batch scheduler started.");
            BatchResponseRepository sqlDB = new BatchResponseRepository();

            while (!stoppingToken.IsCancellationRequested)
            {
                var now = DateTime.Now.ToString("HH:mm");
                var configs = LoadConfigs();
                var tasks = new List<Task>();

                Console.WriteLine(now);
                foreach (var config in configs)
                {
                    // ✅ Estrai "active" in modo sicuro
                    if (!config.TryGetValue("active", out var activeObj) ||
                        !(activeObj is JsonElement activeElement) ||
                        (activeElement.ValueKind != JsonValueKind.True && activeElement.ValueKind != JsonValueKind.False) ||
                        !activeElement.GetBoolean())
                    {
                        continue;
                    }

                    // ✅ Estrai "time" in modo sicuro
                    if (!config.TryGetValue("time", out var timeObj) ||
                        !(timeObj is JsonElement timeElement) ||
                        timeElement.GetString() != now)
                    {
                        continue;
                    }
                    _ = Task.Run(async () =>
                    {
                        try
                        {
                            var id = config["id"].ToString();
                            var endpoint = config["endpoint"].ToString();                                                       

                            // ✅ Estrai "params" come dizionario
                            var paramElement = (JsonElement)config["params"];
                            Console.WriteLine(paramElement);
                            var parameters = JsonSerializer.Deserialize<Dictionary<string, string>>(paramElement.GetRawText());

                            LogBatchEvent($"Execution {id} → {endpoint} con {paramElement}");

                            var client = _httpClientFactory.CreateClient();
                            client.Timeout = TimeSpan.FromMinutes(5);
                            var url = $"http://localhost:8000/batch/run";
                            var payload = new
                            {
                                id,
                                endpoint,
                                @params = parameters
                            };
                            var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
                            var response = await client.PostAsync(url, content);
                            var responseText = await response.Content.ReadAsStringAsync();
                            await SaveBatchResponseAsync(id, responseText);
                            await sqlDB.SaveAsync(id, responseText);
                            _logger.LogInformation($"[{id}] {endpoint} → {response.StatusCode}");
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError($"[{config["id"]}] Errore: {ex.Message}");
                        }
                    });
                }
                if (DateTime.Now.Hour == 18 && _lastEmailSent.Date != DateTime.Today)
                {
                    try
                    {
                        await _mailer.SendDailyBatchReportEmailAsync();
                        _lastEmailSent = DateTime.Today;
                    }
                    catch (Exception ex)
                    {
                        _logger.LogError($"Errore invio email: {ex.Message}");
                    }
                }
                await Task.Delay(TimeSpan.FromMinutes(1), stoppingToken);
                
            }
        }

        private List<Dictionary<string, object>> LoadConfigs()
        {
            if (!File.Exists(_configPath)) return new();
            var json = File.ReadAllText(_configPath);
            if (string.IsNullOrWhiteSpace(json)) return new();
            return JsonSerializer.Deserialize<List<Dictionary<string, object>>>(json);
        }


        private async Task SaveBatchResponseAsync(string id, string responseText)
        {
            await _fileLock2.WaitAsync();

            try
            {
                var responses = new Dictionary<string, object>();

                if (File.Exists(_responsePath))
                {
                    var json = await File.ReadAllTextAsync(_responsePath);
                    try
                    {
                        responses = JsonSerializer.Deserialize<Dictionary<string, object>>(json) ?? new();
                    }
                    catch
                    {
                        Console.WriteLine("[SaveBatchResponse] Il file esistente non è un dizionario JSON valido. Verrà sovrascritto.");
                        responses = new();
                    }
                }

                JsonElement element;
                object parsedResponse;
                Dictionary<string, string> pipelineMap = new();


                try
                {
                    element = JsonSerializer.Deserialize<JsonElement>(responseText);

                    if (element.ValueKind == JsonValueKind.Array)
                    {
                        foreach (var item in element.EnumerateArray())
                        {
                            if (item.ValueKind == JsonValueKind.Object &&
                                item.TryGetProperty("pipeline_name", out var nameProp) &&
                                item.TryGetProperty("status", out var statusProp))
                            {
                                var name = nameProp.GetString();
                                var status = statusProp.GetString();

                                if (!string.IsNullOrEmpty(name))
                                    pipelineMap[name] = status ?? "";
                            }
                        }

                        parsedResponse = JsonSerializer.SerializeToNode(pipelineMap); // 👈 diventa JsonObject
                    }
                    else
                    {
                        parsedResponse = JsonNode.Parse(element.GetRawText());
                    }
                }
                catch
                {
                    parsedResponse = responseText; // fallback: salva come stringa raw
                }
                responses[id] = new
                {
                    timestamp = DateTime.Now.ToString("o"),
                    response = parsedResponse
                };
                var updated = JsonSerializer.Serialize(responses, new JsonSerializerOptions { WriteIndented = true });

                const int maxRetries = 3;
                for (int i = 0; i < maxRetries; i++)
                {
                    try
                    {
                        await File.WriteAllTextAsync(_responsePath, updated);
                        break;
                    }
                    catch (IOException) when (i < maxRetries - 1)
                    {
                        await Task.Delay(200);
                    }
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[SaveBatchResponse] Errore: {ex.Message}");
            }
            finally
            {
                _fileLock2.Release();
            }
        }


        private void LogBatchEvent(string message)
        {
            var logs = new List<Dictionary<string, string>>();
            if (File.Exists(_logPath))
            {
                var json = File.ReadAllText(_logPath);
                logs = JsonSerializer.Deserialize<List<Dictionary<string, string>>>(json);
            }

            logs.Insert(0, new Dictionary<string, string>
            {
                ["timestamp"] = DateTime.Now.ToString("o"),
                ["message"] = message
            });

            File.WriteAllText(_logPath, JsonSerializer.Serialize(logs.Take(100), new JsonSerializerOptions { WriteIndented = true }));
        }
    }
}