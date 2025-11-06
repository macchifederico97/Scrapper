namespace BatchOrchestrator.Models
{
    public class BatchRequest
    {
        public string Id { get; set; } = string.Empty;
        public string Endpoint { get; set; } = string.Empty;
        public Dictionary<string, string> Params { get; set; } = new();

    }
}
