using System.Text.Json;
using Microsoft.Data.Sqlite;

public class BatchResponseRepository
{
    public readonly string _connectionString = "Data Source=data/batch.db";

    public BatchResponseRepository()
    {
        using var conn = new SqliteConnection(_connectionString);
        conn.Open();

        var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            CREATE TABLE IF NOT EXISTS BatchResponses (
                Id TEXT PRIMARY KEY,
                Timestamp TEXT,
                PipelineName TEXT,
                StartTime TEXT,
                FinishTime TEXT,
                DurationMinutes REAL,
                RawJson TEXT
            );
        ";
        cmd.ExecuteNonQuery();
    }

    public async Task SaveAsync(string id, string responseText)
    {
        var doc = JsonDocument.Parse(responseText);
        var root = doc.RootElement;

        using var conn = new SqliteConnection(_connectionString);
        await conn.OpenAsync();

        if (root.ValueKind == JsonValueKind.Array)
        {
            int index = 0;
            foreach (var item in root.EnumerateArray())
            {
                string? pipeline = item.TryGetProperty("pipeline_name", out var p) ? p.GetString() : null;
                string? start = item.TryGetProperty("start_time", out var s) ? s.GetString() : null;
                string? finish = item.TryGetProperty("finish_time", out var f) ? f.GetString() : null;
                double duration = item.TryGetProperty("duration_minutes", out var d) ? d.GetDouble() : 0;

                var cmd = conn.CreateCommand();
                cmd.CommandText = @"
                INSERT OR REPLACE INTO BatchResponses (Id, Timestamp, PipelineName, StartTime, FinishTime, DurationMinutes, RawJson)
                VALUES ($id, $ts, $pipeline, $start, $finish, $duration, $raw);
            ";
                cmd.Parameters.AddWithValue("$id", $"{id}_{index++}");
                cmd.Parameters.AddWithValue("$ts", DateTime.Now.ToString("o"));
                cmd.Parameters.AddWithValue("$pipeline", pipeline ?? "");
                cmd.Parameters.AddWithValue("$start", start ?? "");
                cmd.Parameters.AddWithValue("$finish", finish ?? "");
                cmd.Parameters.AddWithValue("$duration", duration);
                cmd.Parameters.AddWithValue("$raw", item.GetRawText());

                await cmd.ExecuteNonQueryAsync();
            }
        }
        else if (root.ValueKind == JsonValueKind.Object)
        {
            string? pipeline = root.TryGetProperty("pipeline_name", out var p) ? p.GetString() : null;
            string? start = root.TryGetProperty("start_time", out var s) ? s.GetString() : null;
            string? finish = root.TryGetProperty("finish_time", out var f) ? f.GetString() : null;
            double duration = root.TryGetProperty("duration_minutes", out var d) ? d.GetDouble() : 0;

            var cmd = conn.CreateCommand();
            cmd.CommandText = @"
            INSERT OR REPLACE INTO BatchResponses (Id, Timestamp, PipelineName, StartTime, FinishTime, DurationMinutes, RawJson)
            VALUES ($id, $ts, $pipeline, $start, $finish, $duration, $raw);
        ";
            cmd.Parameters.AddWithValue("$id", id);
            cmd.Parameters.AddWithValue("$ts", DateTime.Now.ToString("o"));
            cmd.Parameters.AddWithValue("$pipeline", pipeline ?? "");
            cmd.Parameters.AddWithValue("$start", start ?? "");
            cmd.Parameters.AddWithValue("$finish", finish ?? "");
            cmd.Parameters.AddWithValue("$duration", duration);
            cmd.Parameters.AddWithValue("$raw", responseText);

            await cmd.ExecuteNonQueryAsync();

        }
    }

    public async Task<List<BatchResponseEntry>> GetTodayResponsesAsync()
    {
        var today = DateTime.Today.ToString("yyyy-MM-dd");
        var results = new List<BatchResponseEntry>();

        using var conn = new SqliteConnection(_connectionString);
        await conn.OpenAsync();

        var cmd = conn.CreateCommand();
        cmd.CommandText = @"
            SELECT Id, PipelineName, StartTime, FinishTime, DurationMinutes
            FROM BatchResponses
            WHERE substr(Timestamp, 1, 10) = $today
            ORDER BY Timestamp DESC;
        ";
        cmd.Parameters.AddWithValue("$today", today);

        using var reader = await cmd.ExecuteReaderAsync();
        while (await reader.ReadAsync())
        {
            results.Add(new BatchResponseEntry
            {
                Id = reader.GetString(0),
                PipelineName = reader.GetString(1),
                StartTime = reader.GetString(2),
                FinishTime = reader.GetString(3),
                DurationMinutes = reader.GetDouble(4)
            });
        }

        return results;
    }
}

public class BatchResponseEntry
{
    public required string Id { get; set; }
    public required string PipelineName { get; set; }
    public string? StartTime { get; set; }
    public string? FinishTime { get; set; }
    public double DurationMinutes { get; set; }
}