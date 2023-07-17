"""Entry point."""
import sys

from environs import Env
from loguru import logger

from src.config import RevancedConfig
from src.downloader.factory import DownloaderFactory
from src.downloader.utils import download_revanced
from src.parser import Parser
from src.patches import Patches
from src.utils import AppNotFound, PatcherDownloadFailed


def main() -> None:
    """Entry point."""
    env = Env()
    config = RevancedConfig(env)

    patcher = Patches(config)
    try:
        download_revanced(config, patcher)
    except PatcherDownloadFailed as e:
        logger.error(f"Failed to download {e}")
        sys.exit(1)

    logger.info(f"Will Patch only {patcher.config.apps}")
    for app in patcher.config.apps:
        try:
            logger.info("Trying to build %s" % app)
            parser = Parser(patcher, config)
            app_all_patches, version, is_experimental = patcher.get_app_configs(app)
            patcher.include_exclude_patch(app, parser, app_all_patches)
            downloader = DownloaderFactory.create_downloader(
                app=app, patcher=patcher, config=config
            )
            downloader.download(version, app)
            config.app_versions[app] = version
            logger.info(f"Downloaded {app}, version {version}")
            parser.patch_app(app=app, version=version, is_experimental=is_experimental)
        except AppNotFound as e:
            logger.info(f"Invalid app requested to build {e}")
        except Exception as e:
            logger.exception(f"Failed to build {app} because of {e}")
    if len(config.alternative_youtube_patches) and "youtube" in config.apps:
        for alternative_patch in config.alternative_youtube_patches:
            parser = Parser(patcher, config)
            app_all_patches, version, is_experimental = patcher.get_app_configs(
                "youtube"
            )
            patcher.include_exclude_patch("youtube", parser, app_all_patches)
            was_inverted = parser.invert_patch(alternative_patch)
            if was_inverted:
                logger.info(
                    f"Rebuilding youtube with inverted {alternative_patch} patch."
                )
                parser.patch_app(
                    app="youtube",
                    version=config.app_versions.get("youtube", "latest"),
                    is_experimental=is_experimental,
                    output_prefix="-" + alternative_patch + "-",
                )
            else:
                logger.info(
                    f"Skipping Rebuilding youtube as {alternative_patch} patch was not found."
                )
    if len(config.alternative_youtube_music_patches) and "youtube_music" in config.apps:
        for alternative_patch in config.alternative_youtube_music_patches:
            parser = Parser(patcher, config)
            app_all_patches, version, is_experimental = patcher.get_app_configs(
                "youtube_music"
            )
            patcher.include_exclude_patch("youtube_music", parser, app_all_patches)
            was_inverted = parser.invert_patch(alternative_patch)
            if was_inverted:
                logger.info(
                    f"Rebuilding youtube music with inverted {alternative_patch} patch."
                )
                parser.patch_app(
                    app="youtube_music",
                    version=config.app_versions.get("youtube_music", "latest"),
                    is_experimental=is_experimental,
                    output_prefix="-" + alternative_patch + "-",
                )
            else:
                logger.info(
                    f"Skipping Rebuilding youtube music as {alternative_patch} patch was not found."
                )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.error("Script halted because of keyboard interrupt.")
        sys.exit(1)
