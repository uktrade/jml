from elasticsearch import Elasticsearch
from elasticsearch_dsl import Search

from django.conf import settings

ES_MAX_RESULTS = 100
ES_MIN_SCORE = 0.02
ES_PRE_TAGS = '<strong class="ws-person-search-result__highlight">'
ES_POST_TAGS = '</strong>'


def process_search_terms(search_terms) -> str:
    return search_terms.lower()


def get_search_results(search_terms):
    processed_search_terms = process_search_terms(
        search_terms,
    )

    search_dict = {
        "query": {
            "bool": {
                "should": [
                    {
                        "match": {
                            "name": {
                                "query": processed_search_terms,
                                "boost": 6.0
                            }
                        }
                    },
                    {
                        "match": {
                            "name": {
                                "query": processed_search_terms,
                                "analyzer": "name_synonyms_analyzer",
                                "boost": 4.0
                            }
                        }
                    },
                    {
                        "match": {
                            "contact_email_or_email": processed_search_terms,
                        }
                    },
                    {
                        "multi_match": {
                            "fields": [
                                "name^4",
                                "surname^12",
                                "role_and_group^6",
                                "phone_number_variations^5",
                                "languages^5",
                                "location^4",
                                "formatted_key_skills^4",
                                "formatted_learning_and_development^4",
                                "formatted_additional_responsibilities^4"
                            ],
                            "query": processed_search_terms,
                            "analyzer": "standard"
                        }
                    }
                ],
                "minimum_should_match": 1,
                "boost": 1.0
            }
        },
        "sort": {
            "_score": {
                "order": "desc"
            },
            "name": {
                "order": "asc"
            }
        },
        "highlight": {
            "pre_tags": ES_PRE_TAGS,
            "post_tags": ES_POST_TAGS,
            "number_of_fragments": 0,
            "fields": {
                "name": {},
                "role_and_group": {},
                "contact_email_or_email": {},
                "languages": {},
                "formatted_key_skills": {},
                "formatted_learning_and_development": {},
                "formatted_additional_responsibilities": {}
            }
        },
        "size": ES_MAX_RESULTS,
        "min_score": ES_MIN_SCORE
    }

    search = Search(index=settings.LEGACY_PEOPLE_FINDER_ES_INDEX).using(
        Elasticsearch(
            settings.LEGACY_PEOPLE_FINDER_ES_URL,
        )
    ).update_from_dict(
        search_dict,
    )

    return search.execute()
