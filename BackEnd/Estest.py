from elasticsearch_dsl import connections, Index

connection = connections.create_connection(hosts=['https://localhost:9200'])

index = Index('my-index', using=connection)
index.create()