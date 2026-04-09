# pipewatch

A lightweight CLI for monitoring and alerting on ETL pipeline failures with Slack/email integration.

## Installation

```bash
pip install pipewatch
```

Or install from source:

```bash
git clone https://github.com/yourusername/pipewatch.git
cd pipewatch
pip install -e .
```

## Usage

Configure your monitoring settings:

```bash
pipewatch init
```

Monitor a pipeline command:

```bash
pipewatch run "python my_etl_script.py" --alert-on-failure --slack-webhook <WEBHOOK_URL>
```

Monitor with email notifications:

```bash
pipewatch run "python my_etl_script.py" --email recipient@example.com --smtp-config config.json
```

Schedule periodic checks:

```bash
pipewatch schedule --command "python my_etl_script.py" --interval 1h --alert-channel slack
```

View monitoring history:

```bash
pipewatch history --last 7d
```

## Configuration

Create a `.pipewatch.yml` file in your project root:

```yaml
alerts:
  slack_webhook: https://hooks.slack.com/services/YOUR/WEBHOOK/URL
  email:
    smtp_host: smtp.gmail.com
    smtp_port: 587
    from: alerts@example.com
    to: team@example.com
```

## License

MIT License - see [LICENSE](LICENSE) file for details.