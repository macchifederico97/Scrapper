using System.Text.Json;
using System.Text;
using System.Timers;
using Microsoft.AspNetCore.Mvc;
using System.Collections.Generic;
using System.Threading.Tasks;

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
        public BatchScheduler(ILogger<BatchScheduler> logger, IHttpClientFactory httpClientFactory)
        {
            _logger = logger;
            _httpClientFactory = httpClientFactory;
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
                    tasks.Add(Task.Run(async () =>
                    {
                        try
                        {
                            var id = config["id"].ToString();
                            var endpoint = config["endpoint"].ToString();

                            // ✅ Estrai "params" come dizionario
                            var paramElement = (JsonElement)config["params"];
                            var parameters = JsonSerializer.Deserialize<Dictionary<string, string>>(paramElement.GetRawText());

                            LogBatchEvent($"Execution {id} → {endpoint} con {paramElement}");

                            var client = _httpClientFactory.CreateClient();
                            var url = $"http://localhost:8000/batch/run";
                            var payload = new
                            {
                                id,
                                endpoint,
                                @params = parameters
                            };
                            var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
                            var response = await client.PostAsync(url, content, stoppingToken);
                            var responseText = await response.Content.ReadAsStringAsync();
                            await SaveBatchResponseAsync(id, responseText);
                            _logger.LogInformation($"[{id}] {endpoint} → {response.StatusCode}");
                        }
                        catch (Exception ex)
                        {
                            _logger.LogError($"[{config["id"]}] Errore: {ex.Message}");
                        }
                    }));
                }

                await Task.WhenAll(tasks);
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
            await _fileLock.WaitAsync();

            try
            {
                var responses = new Dictionary<string, object>();

                if (File.Exists(_responsePath))
                {
                    var json = await File.ReadAllTextAsync(_responsePath);
                    responses = JsonSerializer.Deserialize<Dictionary<string, object>>(json) ?? new();
                }

                responses[id] = new
                {
                    timestamp = DateTime.Now.ToString("o"),
                    response = responseText
                };

                var updated = JsonSerializer.Serialize(responses, new JsonSerializerOptions { WriteIndented = true });
                await File.WriteAllTextAsync(_responsePath, updated);
            }
            catch (Exception ex)
            {
                Console.WriteLine($"[SaveBatchResponse] Errore: {ex.Message}");
            }
            finally
            {
                _fileLock.Release();
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