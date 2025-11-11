using System.Net;
using System.Net.Mail;
using System.Text;
using System.Text.Json;

public class BatchReportMailer
{
    private readonly string _responsePath;
    private readonly ILogger<BatchReportMailer> _logger;

    public BatchReportMailer(string responsePath, ILogger<BatchReportMailer> logger)
    {
        _responsePath = responsePath;
        _logger = logger;
    }

    public async Task SendDailyBatchReportEmailAsync()
    {
        if (!File.Exists(_responsePath)) return;
        BatchResponseRepository sqlDB = new BatchResponseRepository();

        var json = await File.ReadAllTextAsync(_responsePath);
        var dict = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(json);
        if (dict == null || dict.Count == 0) return;

        var today = DateTime.Today;
        /*var entries = dict
            .Where(kvp =>
            {
                var timestampStr = kvp.Value.GetProperty("timestamp").GetString();
                return DateTime.TryParse(timestampStr, out var timestamp) && timestamp.Date == today;
            })
            .ToList();*/
        List<BatchResponseEntry> entries = await sqlDB.GetTodayResponsesAsync();
        if (entries.Count == 0) return;

        var html = new StringBuilder();
        html.AppendLine("<h2>GR Bifrost Pipelines status – " + today.ToString("dd MMMM yyyy") + "</h2>");
        html.AppendLine("<table border='1' cellpadding='5' cellspacing='0' style='border-collapse:collapse;'>");
        html.AppendLine("<tr><th>ID</th><th>Pipeline</th><th>Start</th><th>Finish</th><th>Duration (min)</th></tr>");

        foreach (var entry in entries)
        {
            html.AppendLine("<tr>");
            html.AppendLine($"<td>{entry.Id}</td>");
            html.AppendLine($"<td>{entry.PipelineName}</td>");
            html.AppendLine($"<td>{entry.StartTime}</td>");
            html.AppendLine($"<td>{entry.FinishTime}</td>");
            html.AppendLine($"<td>{entry.DurationMinutes:0.00}</td>");
            html.AppendLine("</tr>");
        }

        html.AppendLine("</table>");

        var message = new MailMessage
        {
            From = new MailAddress("noreply@yourdomain.com"),
            Subject = $"GR Bifrost Pipelines status – {today:dd MMMM yyyy}",
            Body = html.ToString(),
            IsBodyHtml = true
        };

        message.To.Add("recipient@nestle.com");

        using var smtp = new SmtpClient("smtp.yourdomain.com")
        {
            Port = 587,
            Credentials = new NetworkCredential("username", "password"),
            EnableSsl = true
        };

        await smtp.SendMailAsync(message);
        _logger.LogInformation("Email giornaliera inviata con successo.");
    }
}