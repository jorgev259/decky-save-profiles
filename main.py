import asyncio
import os
from typing import Any

import aiohttp
import yaml
from decky_loader.settings import SettingsManager

# The decky plugin module is located at decky-loader/backend/decky_loader/plugin
# For easy intellisense checkout the decky-loader code repo
# and add the `decky-loader/backend/decky_loader/plugin/imports` path to `python.analysis.extraPaths` in `.vscode/settings.json`
import decky

LUDOSAVI_MANIFEST_URL: str = "https://raw.githubusercontent.com/mtkennerly/ludusavi-manifest/master/data/manifest.yaml"


class Plugin:
    async def long_running(self):
        await asyncio.sleep(15)
        # Passing through a bunch of random data, just as an example
        await decky.emit("timer_event", "Hello from the backend!", True, 2)

    async def fetch_ludosavi_manifest(self) -> dict[str, Any]:
        last_etag: str | None = self.settings.getSetting("ludosavi_etag")

        headers: dict[str, str] = {}
        if last_etag is not None:
            headers["If-None-Match"] = last_etag

        async with (
            aiohttp.ClientSession() as session,
            session.get(LUDOSAVI_MANIFEST_URL, headers=headers) as response,
        ):
            if response.status == 304:
                decky.logger.info("Ludosavi manifest is up to date.")
                return {}

            if response.status == 200:
                new_etag = response.headers.get("ETag")
                if new_etag is not None:
                    self.settings.setSetting("ludosavi_etag", new_etag)
                manifest = yaml.safe_load(await response.text())
                decky.logger.info("Ludosavi manifest updated.")
                return manifest

            decky.logger.error(
                f"Failed to fetch ludosavi manifest: HTTP {response.status}"
            )
            return {}

    # Asyncio-compatible long-running code, executed in a task when the plugin is loaded
    async def _main(self):
        self.loop = asyncio.get_event_loop()
        self.settings = SettingsManager(
            "save-profiles", decky.DECKY_PLUGIN_SETTINGS_DIR
        )
        decky.logger.info("Hello World!")
        await self.fetch_ludosavi_manifest()

    # Function called first during the unload process, utilize this to handle your plugin being stopped, but not
    # completely removed
    async def _unload(self):
        decky.logger.info("Goodnight World!")

    # Function called after `_unload` during uninstall, utilize this to clean up processes and other remnants of your
    # plugin that may remain on the system
    async def _uninstall(self):
        decky.logger.info("Goodbye World!")

    async def start_timer(self):
        self.loop.create_task(self.long_running())

    # Migrations that should be performed before entering `_main()`.
    async def _migration(self):
        decky.logger.info("Migrating")
        # Here's a migration example for logs:
        # - `~/.config/decky-template/template.log` will be migrated to `decky.decky_LOG_DIR/template.log`
        decky.migrate_logs(
            os.path.join(
                decky.DECKY_USER_HOME, ".config", "decky-template", "template.log"
            )
        )
        # Here's a migration example for settings:
        # - `~/homebrew/settings/template.json` is migrated to `decky.decky_SETTINGS_DIR/template.json`
        # - `~/.config/decky-template/` all files and directories under this root are migrated to `decky.decky_SETTINGS_DIR/`
        decky.migrate_settings(
            os.path.join(decky.DECKY_HOME, "settings", "template.json"),
            os.path.join(decky.DECKY_USER_HOME, ".config", "decky-template"),
        )
        # Here's a migration example for runtime data:
        # - `~/homebrew/template/` all files and directories under this root are migrated to `decky.decky_RUNTIME_DIR/`
        # - `~/.local/share/decky-template/` all files and directories under this root are migrated to `decky.decky_RUNTIME_DIR/`
        decky.migrate_runtime(
            os.path.join(decky.DECKY_HOME, "template"),
            os.path.join(decky.DECKY_USER_HOME, ".local", "share", "decky-template"),
        )
