"""Tools to generate image and store CLIP image embeddings and to conduct a text-to-image search based on these
embeddings."""
import os
import pickle
import numpy as np

from PIL import Image
from sklearn.metrics.pairwise import cosine_similarity
from scipy.special import softmax
from transformers import CLIPProcessor, CLIPModel, CLIPTokenizer

# OPENAI's CLIP model can check whether images match-up with conceptual categories described by text.
MODEL = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
PROCESSOR = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
TOKENIZER = CLIPTokenizer.from_pretrained("openai/clip-vit-base-patch32")

def run_query(prompt, M_images, img_dir,
              anti_prompt="person", img_type='photo', min_prob=0.91):

    """Conducts a text-to-image search across a set of images and their precomputed embeddings. Returns the set of
    image files (and their associated social media ids) that pass the required similarity threshold.

    Parameters
    ----------
    prompt: str
        The search query.
    M_images: np.array
        NumPy matrix of image embeddings.
    img_dir: str
        The directory were the image files are stored. We take as an invariant that the sorted image names in that
        directory align with the rows of `M_images`.
    anti_prompt: str
        A different conceptual category used to counterbalance the query. Qualitatively; setting the anti-prompt
        to `person` for social media images yields greater precision.
    img_type: str
        Is the we're looking for a photo / drawing etc.
    min_prob: float
        The minimum precision probability required to return a match.

    Returns
    -------
    id_to_img: dict
        A mapping between social media ids and matched images that were posted by these users.
    """
    anti_img_type = {'photo': 'drawing', 'drawing': 'photo'}.get(img_type)
    text = [f"a {img_type} of a {prompt}"]
    if anti_prompt is not None:
        if anti_prompt == 'person' and 'woman' in prompt:
            # A hack to improve precision when the prompt is specific for women relative to men.
            anti_prompt = 'man'
        text.append(f"a {img_type} of a {anti_prompt}")
    else:
        text.append(f"not a {img_type} of a {prompt}")

    if anti_img_type is not None:
        # Ensures that the appropriate image types get returned.
        text.extend([f"a {anti_img_type} of a {prompt}"])

    inputs = TOKENIZER(text, padding=True, return_tensors="pt")
    # Computes the text embeddings on on the prompts.
    text_features = MODEL.get_text_features(**inputs)
    # Computes the cosine similarities between the text and image embeddings.
    sim_matrix = cosine_similarity(M_images,  text_features.detach().numpy())
    # Takes the row-wise softmax of the cosine similarities to generate the probabilities.
    probs = softmax(sim_matrix * 100, axis=1).T[0]
    # Returns those matches with a probability that's >= min_prob.
    image_fnames = [os.path.join(img_dir, e) for i, e in enumerate(sorted(os.listdir(img_dir)))
                   if probs[i] >= min_prob]
    id_to_img = {}
    for fname in image_fnames:
        # Extracts what is presumed to be a social media idea from each image.
        id_ = fname.split('/')[-1].split('_')[0]
        if id_ not in id_to_img:
            # Tracks the mapping between social media ids and the first matched image for each id.
            id_to_img[id_] = fname
    return id_to_img



def generate_embedding_matrix(target_id, embedding_dir='image_embeddings'):
    """Computes the matrix of image embeddings from locally stored image files and subsequently saves
    the matrix for text-to-image search lookup."""
    img_dir = f'images_{target_id}'
    img_names = [os.path.join(img_dir, e) for e in sorted(os.listdir(img_dir))]
    M_images = None
    for i in range(0, len(img_names), 10):
        # Iteratively generates the embedding images in batch.
        image_batch = _load_image_batch(img_names, start_index=i, end_index=min(i + 10, len(img_names)))
        inputs = PROCESSOR(images=image_batch, return_tensors="pt")
        image_features = MODEL.get_image_features(**inputs).detach().numpy()
        if M_images is None:
            M_images = image_features
        else:
            # Updates the matrix with the latest embedding batch.
            M_images = np.vstack((M_images, image_features))

    fname = os.path.join(embedding_dir, f'{target_id}.pkl')
    file = open(fname, 'wb')
    pickle.dump(M_images, file)
    file.close()

def _load_image(image_fname):
    """Images must be be converted to RBG format prior processing with CLIP model"""
    return Image.open(image_fname).convert('RGB')

def _load_image_batch(img_names, start_index=0, end_index=100):
    return [_load_image(n) for n in img_names[start_index: end_index]]
