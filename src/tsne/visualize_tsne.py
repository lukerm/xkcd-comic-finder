import os

import numpy as np
from dotenv import load_dotenv
from sklearn.manifold import TSNE

from ..database.weaviate_client import XKCDWeaviateClient
from ..search.query import search_comics

LATENT_DIM_SIZE = 1536  # corresponds to openai small embedding model

cli = XKCDWeaviateClient()
_cli = cli.client

max_id = 3001  # Approx. 3k results ATOW
results = (
    _cli.query
    .get("XKCDComic", ["comic_id", "title", "image_url", "explanation", "transcript"])
    .with_where({
        "path": ["comic_id"],
        "operator": "LessThan",
        "valueInt": max_id
    })
    .with_additional(["vector"])
    .with_limit(max_id)
    .do()
)
results = results.get("data", {}).get("Get", {}).get("XKCDComic", [])




X = np.zeros(shape=(3_000, LATENT_DIM_SIZE))
ids, titles = [], []
for i, res in enumerate(results):
    X[i, :] = res['_additional']['vector']
    ids.append(res['comic_id'])
    titles.append(res['title'])

import openai
from dotenv import load_dotenv; load_dotenv()
client_openai = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
queries = ["automobile", "centripetal", "correlation", "flying", "programming", "USB"]
Q = np.zeros(shape=(len(queries), LATENT_DIM_SIZE))
for i, q in enumerate(queries):
    response = client_openai.embeddings.create(
        model="text-embedding-3-small",
        input=q
    )
    Q[i, :] = response.data[0].embedding

# Combine data sets
XQ = np.concatenate([X, Q], axis=0)
ids.extend([-1]*len(Q))
titles.extend(queries)


tsne = TSNE(n_components=2, random_state=2025)
XQ_reduced = tsne.fit_transform(XQ)
print(XQ_reduced.shape)



limit = 10
comic_groups = {}
for q in queries:
    retrieved = search_comics(client=cli, query=q, limit=limit, alpha=0.5)
    for comic in retrieved:
        comic_groups[comic['comic_id']] = q



import matplotlib; matplotlib.get_backend(); matplotlib.use('Qt5Agg')
import pandas as pd
import seaborn as sns





df_tsne = pd.DataFrame(XQ_reduced, columns = ['dim1', 'dim2'])

plot_labels = [comic_groups.get(comic_id, 'Other') for comic_id in ids[:-len(queries)]] + titles[-len(queries):]
alphas = [0.2 if label == 'Other' else 0.9 for label in plot_labels]
df_tsne['Category'] = plot_labels
df_tsne['Title'] = titles


ax = sns.scatterplot(x='dim1', y='dim2', data=df_tsne,
                    hue='Category', #hue_order=plot_categories + ['Other'],
                    # alpha=alphas)
                    alpha=0.75)

# Label specific query points
for i, row in df_tsne.tail(len(queries)).iterrows():
    ax.annotate(f'Q:{row["Title"]}', (row['dim1'], row['dim2']), xytext=(5, 5), textcoords='offset points')
    # ax.annotate(text=f'foo', xy=(row['dim1'], row['dim2']), xytext=(5, 5), textcoords='offset points')
