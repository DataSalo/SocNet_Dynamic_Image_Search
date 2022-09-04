"""Dash app to display a specified precomputed network, with text-to-image search that dynamically embeds
all matched images into the nodes."""
import os
import dash
import dash_cytoscape as cyto
from dash import html, dcc
from dash.dependencies import Input, Output, State
import base64
import json
import pickle

from clip_embedding_utils import run_query

# (TODO): Find better way to specify network id argument
TARGET_ID = input('\nEnter scrapped network id (example: 414930480):\n')

def b64_image(image_filename):
    """Loads local image for cytoscape insertion. Otherwise the image won't show locally."""
    with open(image_filename, 'rb') as f:
        image = f.read()

    return 'data:image/png;base64,' + base64.b64encode(image).decode('utf-8')

def load_net(target_id, query=None, embedding_dir='image_embeddings', json_dir='net_json'):
    """Load a procomputed network in cytoscape json format. Returns network and stylesheet.
    If text-to-image query is specified, and the matched images are visualized within
    nodes of the network."""
    stylesheet = [{"selector": "[category='regular']","style": {"background-color": "pink",}}]
    fname = os.path.join(json_dir, f'{target_id}.json')
    with open(fname) as json_file:
        network = json.load(json_file)

    if not query:
        return network, stylesheet

    fname = os.path.join(embedding_dir, f'{target_id}.pkl')
    M_images = pickle.load(open(fname,'rb'))
    # Runs a text-to-image query.
    id_to_images = run_query(query, M_images, f'images_{target_id}')
    for element in network:
        data = element['data']
        id_ = data.get('id')
        if not id_:
            # Reached the network edges.
            break

        if id_ in id_to_images:
            # Found a match.
            data['category'] = 'query_match'
            match_image = id_to_images[id_]
            data['match_image'] = match_image
            # Embeds the matched image in the associated node.
            selector = {"selector": f"#{id_}",
                        "style": {"background-fit": "cover",
                                  "background-image": f"{b64_image(match_image)}",}}
            stylesheet.append(selector)
    return network, stylesheet

def generate_cytoscape_network(query=None):
    network, stylesheet = load_net(TARGET_ID, query)
    return cyto.Cytoscape(
        id='friend_of_friend_network',
        layout={'name': 'cose-bilkent'},
        style={'width': '100%', 'height': '400px'},
        stylesheet=stylesheet,
       elements=network
    )

def get_search_form():
    # Search form to initiate the query.
    return html.Div([
        html.Div(dcc.Input(id='input-on-submit', type='text', placeholder='Enter Image Description')),
        html.Button('Image Search', id='submit-val', n_clicks=0),
    ])


app = dash.Dash(__name__)

@app.callback(
    Output('friend_of_friend_network', 'elements'),
    Output('friend_of_friend_network', 'stylesheet'),
    Input('submit-val', 'n_clicks'),
    State('input-on-submit', 'value')
)
def update_output(n_clicks, query):
    network, stylesheet = load_net(TARGET_ID, query)
    return (network, stylesheet)

@app.callback(Output("cytoscape-tapNodeData-output", "children"), [Input("friend_of_friend_network", "tapNodeData")])
def displayTapNodeData(data):
    """Displays linked profile information whenever a node is clicked"""
    if data:
        name = data["name"]

        vk_url = data['url']
        name_link = html.A(html.H3(name), target="_blank", href=vk_url)
        result = [name_link]
        img_src = data.get('image') if 'match_image' not in data else data['match_image']

        if img_src:
            img_div = html.Div(html.Img(src=f"{b64_image(img_src)}", height=400, width=400))
            result.append(img_div)
        return html.Div(result)


cyto.load_extra_layouts()


style_list = []

app.layout = html.Div([
    get_search_form(),
    generate_cytoscape_network(),
    html.Div(id="cytoscape-tapNodeData-output"),

])

if __name__ == '__main__':
    app.run_server(debug=True)
