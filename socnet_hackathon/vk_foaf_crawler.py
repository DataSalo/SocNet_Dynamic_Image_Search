import os
import json
from vk_crawler_utils import  vk_login, get_profile_name, scrape_friends, get_orc_images
from clip_embedding_utils import generate_embedding_matrix

def scrape_friend_friend_graph(id_, email, pwd):
    """Logins into VK via Selenium using `email` and `pwd`. Afterwards, accesses the VK profile
    of the user associated with `vk` and scrapes all existing edge connections between that user's
    friends. Additionally, the script downloads and stores all top profile images for further analysis.
    The scraped FoaF network is stored in a JSON format compatible with Cytoscape.js.
    """
    vk_login(email, pwd)
    print('Scrapping central target')
    central_target = get_profile_name(id_.strip())
    print('Scrapping friends of target')

    friends = scrape_friends(id_)
    friend_ids = {f['vkId'] for f in friends}
    print(f'Identified {len(friend_ids)} friends.')
    friend_to_friend = {}
    print('Scraping friend-of-a-friend network')
    for friend_id in friend_ids:
        fof_ids = {f['vkId'] for f in scrape_friends(friend_id)}
        overlap = friend_ids & fof_ids
        if(overlap):
            friend_to_friend[friend_id] = overlap
            break

    # Directory where all images associated with target and friends of target will be be stored.
    img_dir = f'images_{id_}'
    os.makedirs(img_dir, exist_ok=True)
    print('Downloading images associated with the target and friends')
    id_to_imgs = {id_: get_orc_images(id_, img_dir)}
    for f_id in friend_ids:
        id_to_imgs[f_id] = get_orc_images(f_id, img_dir)
        break

    print('Computing and caching the downloaded image embeddings.')
    generate_embedding_matrix(id_)
    print('Saving friend-of-a-friend network.')
    gen_cytscape_json(central_target, friends,  friend_to_friend, id_to_imgs)

def gen_cytscape_json(central_target, friends,  friend_to_friend, id_to_imgs,
                      json_dir='net_json'):
    """The scraped FoaF network is stored in a JSON format compatible with Cytoscape.js."""
    nodes = []
    target_id = central_target['vkId']
    for person in [central_target] + friends:
        id_ = person['vkId']
        node_data = {'id': id_, 'name': person['name'], 'url': person['vk_link'],
                     'image': id_to_imgs.get(id_, [''])[0],
                     'category': 'regular' if id_ != target_id else 'central_target'}
        nodes.append({'data': node_data})

    # NOTE: We only include edges between friends the target and other friends. We skip over the edges between
    # friends and the target. Otherwise the final edge-dense visualization will be unmanageable.
    edges = []
    for id1, fof in friend_to_friend.items():
        edges.extend([{'data': {'source': id1, 'target': id2}} for id2 in fof])

    fname = os.path.join(json_dir, f'{target_id}.json')
    with open(fname, 'w') as f:
        json.dump(nodes + edges, f)


if __name__ == '__main__':
    id_ = input('\nEnter VK id (example: 414930480):\n')
    email = input('\nEnter VK email:\n')
    pwd = input('\nEnter VK password:\n')
    scrape_friend_friend_graph(id_, email, pwd)
