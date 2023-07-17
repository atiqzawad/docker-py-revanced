"""Revanced Patches."""
import json
import subprocess
from typing import Any, Dict, List, Tuple

from loguru import logger
from requests import Session

from src.config import RevancedConfig
from src.utils import AppNotFound, handle_response


class Patches(object):
    """Revanced Patches."""

    _revanced_app_ids = {
        "com.reddit.frontpage": "reddit",
        "com.ss.android.ugc.trill": "tiktok",
        "com.twitter.android": "twitter",
        "de.dwd.warnapp": "warnwetter",
        "com.spotify.music": "spotify",
        "com.awedea.nyx": "nyx-music-player",
        "ginlemon.iconpackstudio": "icon_pack_studio",
        "com.ticktick.task": "ticktick",
        "tv.twitch.android.app": "twitch",
        "com.myprog.hexedit": "hex-editor",
        "co.windyapp.android": "windy",
        "org.totschnig.myexpenses": "my-expenses",
        "com.backdrops.wallpapers": "backdrops",
        "com.ithebk.expensemanager": "expensemanager",
        "net.dinglisch.android.taskerm": "tasker",
        "net.binarymode.android.irplus": "irplus",
        "com.vsco.cam": "vsco",
        "com.zombodroid.MemeGenerator": "meme-generator-free",
        "com.teslacoilsw.launcher": "nova_launcher",
        "eu.faircode.netguard": "netguard",
        "com.instagram.android": "instagram",
        "com.nis.app": "inshorts",
        "com.facebook.orca": "facebook",
        "com.google.android.apps.recorder": "grecorder",
        "tv.trakt.trakt": "trakt",
        "com.candylink.openvpn": "candyvpn",
        "com.sony.songpal.mdr": "sonyheadphone",
        "com.dci.dev.androidtwelvewidgets": "androidtwelvewidgets",
        "io.yuka.android": "yuka",
        "free.reddit.news": "relay",
        "com.rubenmayayo.reddit": "boost",
        "com.andrewshu.android.reddit": "rif",
        "com.laurencedawson.reddit_sync": "sync",
        "ml.docilealligator.infinityforreddit": "infinity",
        "me.ccrama.redditslide": "slide",
        "com.onelouder.baconreader": "bacon",
    }
    revanced_app_ids = {
        key: (value, "_" + value) for key, value in _revanced_app_ids.items()
    }
    _revanced_extended_app_ids = {
        "com.google.android.youtube": "youtube",
        "com.google.android.apps.youtube.music": "youtube_music",
        "com.mgoogle.android.gms": "microg",
        "com.reddit.frontpage": "reddit",
    }
    revanced_extended_app_ids = {
        key: (value, "_" + value) for key, value in _revanced_extended_app_ids.items()
    }

    @staticmethod
    def check_java() -> None:
        """Check if Java17 is installed."""
        try:
            jd = subprocess.check_output(
                ["java", "-version"], stderr=subprocess.STDOUT
            ).decode("utf-8")
            jd = jd[1:-1]
            if "Runtime Environment" not in jd:
                raise subprocess.CalledProcessError(-1, "java -version")
            if "17" not in jd:
                raise subprocess.CalledProcessError(-1, "java -version")
            logger.debug("Cool!! Java is available")
        except subprocess.CalledProcessError:
            logger.debug("Java 17 Must be installed")
            exit(-1)

    # noinspection DuplicatedCode
    def fetch_patches(self) -> None:
        """Function to fetch all patches."""
        session = Session()
        if self.config.dry_run:
            logger.debug("fetching all patches from local file")
            with open("patches.json") as f:
                patches = json.load(f)
        else:
            url = "https://raw.githubusercontent.com/revanced/revanced-patches/main/patches.json"
            logger.debug(f"fetching all patches from {url}")
            response = session.get(url)
            handle_response(response)
            patches = response.json()

        for app_name in (self.revanced_app_ids[x][1] for x in self.revanced_app_ids):
            setattr(self, app_name, [])
        setattr(self, "universal_patch", [])

        for patch in patches:
            if not patch["compatiblePackages"]:
                p = {x: patch[x] for x in ["name", "description"]}
                p["app"] = "universal"
                p["version"] = "all"
                getattr(self, "universal_patch").append(p)
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in self.revanced_app_ids:
                    app_name = self.revanced_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)
        if self.config.dry_run:
            extended_patches = patches
        else:
            if self.config.build_extended:
                url = "https://raw.githubusercontent.com/inotia00/revanced-patches/revanced-extended/patches.json"
            else:
                url = "https://raw.githubusercontent.com/revanced/revanced-patches/main/patches.json"
            response = session.get(url)
            handle_response(response)
            extended_patches = response.json()
        for app_name in (
            self.revanced_extended_app_ids[x][1] for x in self.revanced_extended_app_ids
        ):
            setattr(self, app_name, [])

        for patch in extended_patches:
            for compatible_package, version in [
                (x["name"], x["versions"]) for x in patch["compatiblePackages"]
            ]:
                if compatible_package in self.revanced_extended_app_ids:
                    app_name = self.revanced_extended_app_ids[compatible_package][1]
                    p = {x: patch[x] for x in ["name", "description"]}
                    p["app"] = compatible_package
                    p["version"] = version[-1] if version else "all"
                    getattr(self, app_name).append(p)

        for app_name, app_id in self.revanced_extended_app_ids.values():
            n_patches = len(getattr(self, app_id))
            logger.debug(f"Total patches in {app_name} are {n_patches}")
        for app_name, app_id in self.revanced_app_ids.values():
            n_patches = len(getattr(self, app_id))
            logger.debug(f"Total patches in {app_name} are {n_patches}")
        n_patches = len(getattr(self, "universal_patch"))
        logger.debug(f"Total universal patches are {n_patches}")

    def __init__(self, config: RevancedConfig) -> None:
        self.config = config
        self.check_java()
        self.fetch_patches()
        if self.config.dry_run:
            self.config.apps = list(self._revanced_app_ids.values())

    def get(self, app: str) -> Tuple[List[Dict[str, str]], str]:
        """Get all patches for the given app.

        :param app: Name of the application
        :return: Patches
        """
        logger.debug("Getting patches for %s" % app)
        app_names = {value[0]: value[1] for value in self.revanced_app_ids.values()}
        app_names.update(
            {value[0]: value[1] for value in self.revanced_extended_app_ids.values()}
        )

        if not (app_name := app_names.get(app)):
            raise AppNotFound(app)
        patches = getattr(self, app_name)
        version = "latest"
        try:
            version = next(i["version"] for i in patches if i["version"] != "all")
            logger.debug(f"Recommended Version for patching {app} is {version}")
        except StopIteration:
            pass
        return patches, version

    # noinspection IncorrectFormatting
    def include_exclude_patch(
        self, app: str, parser: Any, patches: List[Dict[str, str]]
    ) -> None:
        """Include and exclude patches for a given app.

        :param app: Name of the app
        :param parser: Parser Obj
        :param patches: All the patches of a given app
        """
        if self.config.build_extended and app in self.config.extended_apps:
            excluded_patches = self.config.env.list(
                f"EXCLUDE_PATCH_{app}_EXTENDED".upper(), []
            )
            included_patches = self.config.env.list(
                f"INCLUDE_PATCH_{app}_EXTENDED".upper(), []
            )
        else:
            excluded_patches = self.config.env.list(f"EXCLUDE_PATCH_{app}".upper(), [])
            included_patches = self.config.env.list(f"INCLUDE_PATCH_{app}".upper(), [])
        for patch in patches:
            normalized_patch = patch["name"].lower().replace(" ", "-")
            parser.include(
                normalized_patch
            ) if normalized_patch not in excluded_patches else parser.exclude(
                normalized_patch
            )
        for normalized_patch in included_patches:
            parser.include(normalized_patch) if normalized_patch not in getattr(
                self, "universal_patch", []
            ) else ()
        excluded = parser.get_excluded_patches()
        if excluded:
            logger.debug(f"Excluded patches {excluded} for {app}")
        else:
            logger.debug(f"No excluded patches for {app}")

    def get_app_configs(self, app: str) -> Tuple[List[Dict[str, str]], str, bool]:
        """Get Configurations for a given app.

        :param app: Name of the application
        :return: All Patches , Its version and whether it is
            experimental
        """
        experiment = False
        total_patches, recommended_version = self.get(app=app)
        env_version = self.config.env.str(f"{app}_VERSION".upper(), None)
        if env_version:
            logger.debug(f"Picked {app} version {env_version} from env.")
            if (
                env_version == "latest"
                or env_version > recommended_version
                or env_version < recommended_version
            ):
                experiment = True
            recommended_version = env_version
        return total_patches, recommended_version, experiment
