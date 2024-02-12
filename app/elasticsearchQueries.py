from elasticsearch import AsyncElasticsearch


async def checkPing(es: AsyncElasticsearch):
    asd = await es.ping()
    if not asd:
        raise ValueError("Connection failed,Wrong IP,Change from virtual machine ")
