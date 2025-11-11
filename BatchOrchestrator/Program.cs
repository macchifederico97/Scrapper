using BatchOrchestrator.Access;
using BatchOrchestrator.Services;

var builder = WebApplication.CreateBuilder(args);
builder.Logging.AddConsole();

builder.Services.AddControllers();
builder.Services.AddHttpClient<IPythonApiAccess, PythonApiAccess>();
builder.Services.AddSingleton<BatchReportMailer>(sp =>
{
    var logger = sp.GetRequiredService<ILogger<BatchReportMailer>>();
    return new BatchReportMailer("data/batch_response.json", logger);
});
builder.Services.AddSingleton<BatchResponseRepository>();
builder.Services.AddHostedService<BatchScheduler>();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var app = builder.Build();



if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();
app.UseStaticFiles();
app.UseAuthorization();
app.MapControllers();


app.Run();