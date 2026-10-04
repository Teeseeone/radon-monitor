"""Register the bundled card without duplicating existing resources."""
from urllib.parse import urlsplit


async def async_register_card_resource(resources, card_url):
    """Load resources, update this card's versions, or add it once."""
    await resources.async_get_info()
    path = urlsplit(card_url).path
    matches = [item for item in resources.async_items()
               if urlsplit(item.get("url", "")).path == path
               and not urlsplit(item.get("url", "")).netloc]
    if matches:
        for item in matches:
            if item.get("url") != card_url or item.get("type") != "module":
                await resources.async_update_item(item["id"], {"url": card_url, "res_type": "module"})
    else:
        await resources.async_create_item({"url": card_url, "res_type": "module"})
