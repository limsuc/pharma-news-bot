from pharma_news_bot.config import load_settings
from pharma_news_bot.logging_setup import configure_logging
from pharma_news_bot.pipeline import NewsPipeline


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_dir)
    sent_count = NewsPipeline(settings).run()
    print(f"Sent {sent_count} news items.")


if __name__ == "__main__":
    main()

