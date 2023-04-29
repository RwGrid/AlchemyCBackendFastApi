import os

from dotenv import dotenv_values
from elasticsearch import AsyncElasticsearch

assert os.path.isfile("./.env")
ELASTIC_CONFIG: dict = dotenv_values("./.env")


class ElasticSearchSingelton:
    _instance = None
    es_client=None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ElasticSearchSingelton, cls).__new__(
                cls, *args, **kwargs
            )
            cls.es_client: AsyncElasticsearch = (
                ElasticSearchSingelton.initialize_elastic_instance()
            )
        return cls._instance

    @staticmethod
    def initialize_elastic_instance() -> AsyncElasticsearch:
        # print("elastic config :" + str(ELASTIC_CONFIG))
        es = AsyncElasticsearch(
            hosts=ELASTIC_CONFIG["elastic_host"],
            http_auth=(
                ELASTIC_CONFIG["elastic_username"],
                ELASTIC_CONFIG["elastic_password"],
            ),
            verify_certs=False,
            ca_certs="ca.crt",
        )#https://github.com/elastic/elasticsearch-py/issues/712
        return es
