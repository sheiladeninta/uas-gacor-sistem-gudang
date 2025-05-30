import graphene
from schema.queries import Query
from schema.mutations import Mutation

schema = graphene.Schema(query=Query, mutation=Mutation)
