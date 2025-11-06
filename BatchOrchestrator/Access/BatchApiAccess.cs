using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace BatchOrchestrator.Access;

public interface IPythonApiAccess
{
    Task<string> CallPythonBatchAsync(string endpoint, Dictionary<string, string> parameters, string id);
    Task<string> CallPythonGetAsync(string endpoint);
    Task<string> CallPythonPostAsync(string endpoint, object payload);
    Task<string> CallHealthzAsync();
    Task<string> CallRerunAsync(string pipelineName, string bifrostInstance);
    Task<string> CallRuntimeAsync(string pipelineName, string bifrostInstance);
    Task<string> CallGetIDAsync(string pipelineName, string bifrostInstance, string filter);
    Task<string> CallPipelineStatusAsync(string filter, string bifrostInstance);
    Task<string> CallLastLogAsync(string pipelineName, string bifrostInstance);
    Task<string> CallFullExtractAsync(string bifrostInstance, string filter);
    Task<string> CallUserStatusAsync(string visualfabriqInstance);
}

public class PythonApiAccess : IPythonApiAccess
{
    private readonly HttpClient _httpClient;
    private const string BaseUrl = "http://localhost:8000";

    public PythonApiAccess(HttpClient httpClient)
    {
        _httpClient = httpClient;
    }

    public async Task<string> CallPythonBatchAsync(string endpoint, Dictionary<string, string> parameters, string id)
    {
        var payload = new
        {
            id,
            endpoint,
            @params = parameters
        };

        var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync($"{BaseUrl}/batch/run", content);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallPythonGetAsync(string endpoint)
    {
        var response = await _httpClient.GetAsync($"{BaseUrl}{endpoint}");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallPythonPostAsync(string endpoint, object payload)
    {
        var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync($"{BaseUrl}{endpoint}", content);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }
    public async Task<string> CallHealthzAsync()
    {
        var response = await _httpClient.GetAsync($"{BaseUrl}/healthz");
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallRerunAsync(string pipelineName, string bifrostInstance)
    {
        var payload = new Dictionary<string, string>
        {
            { "pipeline_name", pipelineName },
            { "bifrost_instance", bifrostInstance }
        };
        var content = new StringContent(JsonSerializer.Serialize(payload), Encoding.UTF8, "application/json");
        var response = await _httpClient.PostAsync($"{BaseUrl}/api/rerun", content);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallRuntimeAsync(string pipelineName, string bifrostInstance)
    {
        var url = $"{BaseUrl}/api/runtime?pipeline_name={pipelineName}&bifrost_instance={bifrostInstance}";
        var response = await _httpClient.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallGetIDAsync(string pipelineName, string bifrostInstance, string filter)
    {
        var url = $"{BaseUrl}/api/getID?pipeline_name={pipelineName}&bifrost_instance={bifrostInstance}&filter={filter}";
        var response = await _httpClient.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallPipelineStatusAsync(string filter, string bifrostInstance)
    {
        var url = $"{BaseUrl}/api/pipelineStatus?filter={filter}&bifrost_instance={bifrostInstance}";
        var response = await _httpClient.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallLastLogAsync(string pipelineName, string bifrostInstance)
    {
        var url = $"{BaseUrl}/api/lastLog?pipeline_name={pipelineName}&bifrost_instance={bifrostInstance}";
        var response = await _httpClient.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallFullExtractAsync(string bifrostInstance, string filter)
    {
        var url = $"{BaseUrl}/api/pipelineFullExtract?bifrost_instance={bifrostInstance}&filter={filter}";
        var response = await _httpClient.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }

    public async Task<string> CallUserStatusAsync(string visualfabriqInstance)
    {
        var url = $"{BaseUrl}/api/userStatus?visualfabriq_instance={visualfabriqInstance}";
        var response = await _httpClient.GetAsync(url);
        response.EnsureSuccessStatusCode();
        return await response.Content.ReadAsStringAsync();
    }
}