using Microsoft.AspNetCore.Mvc;
using BatchOrchestrator.Access;
using BatchOrchestrator.Models;
using System.Text.Json;

namespace BatchOrchestrator.Controllers
{
    [ApiController]
    [Route("batch")]
    public class BatchController : ControllerBase
    {
        private readonly IPythonApiAccess _apiAccess;

        public BatchController(IPythonApiAccess apiAccess)
        {
            _apiAccess = apiAccess;
        }

        [HttpPost("run")]
        public async Task<IActionResult> RunBatch([FromBody] BatchRequest request)
        {
            var result = await _apiAccess.CallPythonBatchAsync(request.Endpoint, request.Params, request.Id);
            return Ok(new { status = "ok", response = result });
        }

        [HttpGet("configs")]
        public IActionResult GetConfigs()
        {
            var path = "data/batch_config.json";
            if (!System.IO.File.Exists(path))
                return Ok(new List<object>());

            var json = System.IO.File.ReadAllText(path);
            return Content(json, "application/json");
        }
        [HttpGet("logs")]
        public IActionResult GetLogs()
        {
            var path = "data/batch_log.json";
            if (!System.IO.File.Exists(path))
                return Ok(new List<object>());

            var json = System.IO.File.ReadAllText(path);
            return Content(json, "application/json");
        }

        [HttpGet("responses")]
        public IActionResult GetResponses()
        {
            var path = "data/batch_response.json";
            if (!System.IO.File.Exists(path))
                return Ok(new List<object>());

            var json = System.IO.File.ReadAllText(path);
            return Content(json, "application/json");
        }

        [HttpPost("toggle")]
        public IActionResult toggle([FromBody] JsonElement request)
        {
            var id = request.GetProperty("id").GetString();
            var path = "data/batch_config.json";
            var json = System.IO.File.ReadAllText(path);
            var list = JsonSerializer.Deserialize<List<JsonElement>>(json);
            //var updated = new Dictionary<string, object>();

            var updatedList = new List<JsonElement>();

            foreach (var item in list)
            {
                var currentId = item.GetProperty("id").GetString();

                if (currentId == id)
                {
                    var updated = new Dictionary<string, object>();

                    foreach (var prop in item.EnumerateObject())
                    {
                        if (prop.Name == "active")
                        {
                            var currentValue = prop.Value.GetBoolean();
                            updated["active"] = !currentValue; // inverti
                        }
                        else
                        {
                            updated[prop.Name] = prop.Value;
                        }
                    }

                    var jsonObj = JsonSerializer.Serialize(updated);
                    var newElement = JsonSerializer.Deserialize<JsonElement>(jsonObj);
                    updatedList.Add(newElement);
                }
                else
                {
                    updatedList.Add(item); // non modificare
                }
            }
            var updatedJson = JsonSerializer.Serialize(updatedList, new JsonSerializerOptions { WriteIndented = true });
            System.IO.File.WriteAllText("data/batch_config.json", updatedJson);

            return Ok(new { id });
        }

        [HttpPost("delete")]
        public IActionResult deleteConfig([FromBody] JsonElement request)
        {
           
            if (!request.TryGetProperty("id", out var idProp))
                    return BadRequest("Missing 'id'");
            var id = idProp.GetString();
            var path = "data/batch_config.json";
            var json = System.IO.File.ReadAllText(path);
            var list = JsonSerializer.Deserialize<List<JsonElement>>(json);

            var updatedList = new List<JsonElement>();

            foreach (var item in list)
            {
                var currentId = item.GetProperty("id").GetString();

                if (currentId == id)
                {
                    var updated = new Dictionary<string, object>();

                    foreach (var prop in item.EnumerateObject())
                    {
                        updated[prop.Name] = prop.Name == "delete" ? true : prop.Value;
                    }

                    if (!updated.ContainsKey("delete"))
                        updated["delete"] = true;

                    var newJson = JsonSerializer.Serialize(updated);
                    updatedList.Add(JsonSerializer.Deserialize<JsonElement>(newJson));
                }
                else
                {
                    updatedList.Add(item);
                }
            }

            System.IO.File.WriteAllText(path, JsonSerializer.Serialize(updatedList, new JsonSerializerOptions { WriteIndented = true }));
            return Ok(new { deleted = id });



        }

        [HttpPost("save")]
        public IActionResult SaveConfig([FromBody] JsonElement data)
        {
            var path = "data/batch_config.json";
            List<JsonElement> configs;

            if (System.IO.File.Exists(path))
            {
                var existing = System.IO.File.ReadAllText(path);
                configs = JsonSerializer.Deserialize<List<JsonElement>>(existing) ?? new();
            }
            else
            {
                configs = new List<JsonElement>();
            }

            var newId = $"id_{configs.Count + 1:00000}";
            var updated = data.GetProperty("endpoint").ToString();
            var obj = JsonSerializer.Deserialize<Dictionary<string, object>>(data.GetRawText());
            obj["id"] = newId;
            configs.Add(JsonSerializer.Deserialize<JsonElement>(JsonSerializer.Serialize(obj)));

            System.IO.File.WriteAllText(path, JsonSerializer.Serialize(configs, new JsonSerializerOptions { WriteIndented = true }));
            return Ok(new { status = "saved", id = newId });
        }

        [HttpGet("healthz")]
        public async Task<IActionResult> HealthCheck()
        {
            var result = await _apiAccess.CallHealthzAsync();
            return Ok(new { status = "ok", response = result });
        }

        [HttpPost("app/rerun")]
        public async Task<IActionResult> Rerun([FromBody] JsonElement request)
        {
            var pipeline = request.GetProperty("pipeline_name_rerun").GetString();
            var bifrost = request.GetProperty("bifrost_instance").GetString();
            var result = await _apiAccess.CallRerunAsync(pipeline, bifrost);
            return Ok(result);
        }

        [HttpGet("app/runtime")]
        public async Task<IActionResult> Runtime([FromQuery] string pipeline_name, [FromQuery] string bifrost_instance)
        {
            var result = await _apiAccess.CallRuntimeAsync(pipeline_name, bifrost_instance);
            return Ok(result);
        }

        [HttpGet("app/getID")]
        public async Task<IActionResult> GetID([FromQuery] string pipeline_name, [FromQuery] string bifrost_instance, [FromQuery] string filter)
        {
            var result = await _apiAccess.CallGetIDAsync(pipeline_name, bifrost_instance, filter);
            return Ok(result);
        }

        [HttpGet("app/status")]
        public async Task<IActionResult> Status([FromQuery] string filter, [FromQuery] string bifrost_instance)
        {
            var result = await _apiAccess.CallPipelineStatusAsync(filter, bifrost_instance);
            return Ok(result);
        }

        [HttpGet("app/lastLog")]
        public async Task<IActionResult> LastLog([FromQuery] string pipeline_name, [FromQuery] string bifrost_instance)
        {
            var result = await _apiAccess.CallLastLogAsync(pipeline_name, bifrost_instance);
            return Ok(result);
        }

        [HttpGet("app/fullExtract")]
        public async Task<IActionResult> FullExtract([FromQuery] string bifrost_instance, [FromQuery] string filter)
        {
            var result = await _apiAccess.CallFullExtractAsync(bifrost_instance, filter);
            return Ok(result);
        }

        [HttpGet("app/userStatus")]
        public async Task<IActionResult> UserStatus([FromQuery] string visualfabriq_instance)
        {
            var result = await _apiAccess.CallUserStatusAsync(visualfabriq_instance);
            return Ok(result);
        }

    }
}
