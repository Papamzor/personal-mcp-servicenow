from service_now_api import make_nws_request, NWS_API_BASE
from utils import getKeywords

async def changesfortext(inputText: str):
    """Get changes based on input text."""
    keywords = getKeywords(inputText)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields=number,short_description&sysparm_query=short_descriptionCONTAINS{keyword}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def getshortdescforchange(inputincident: str):
    """Get short_description for a given change based on input change number."""
    keywords = getKeywords(inputincident)
    for keyword in keywords:
        url = f"{NWS_API_BASE}/api/now/table/change_request?sysparm_fields=short_description&sysparm_query=number={inputincident}"
        data = await make_nws_request(url)
        if data:
            return data
    return "Unable to fetch alerts or no alerts found."

async def similarchangefortext(inputincident: str):
    """Get similar changes based on given change."""
    inputText = await getshortdescforchange(inputincident)
    return await similarchangefortext(inputText)
