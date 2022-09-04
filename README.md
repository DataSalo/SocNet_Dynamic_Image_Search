# SocNet Dynamic Image Search
Automatically identify and highlight targets (Russian soldiers, right-wing extremists etc) in visualized social networks

## Team Members
UlyssesNYC
https://medium.com/@DataSalo

## Tool Description
This sections discusses the purpose and motivation for the tool, and how it addresses a tool need you've identified.

## Installation

1. Make sure you have Python version 3.8 or greater installed

2. Download the tool's repository using the command:

        git clone https://github.com/DataSalo/SocNet_Dynamic_Image_Search.git

3. Move to the tool's directory and install the necessary requirement

        cd SocNet_Dynamic_Image_Search
        pip install -r requirements.txt
4. For those users who also wish to carry out a Selenium driven friend-of-a-friend VK search, please follow the instructions [here](https://selenium-python.readthedocs.io/installation.html) for Selenium driver installation

## Usage
### Socnet App Usage for Network Visualization with Dynamic Image Search
1. Go to `SocNet_Dynamic_Image_Search/code` and run `python socnet_app.py`.
2. Go to http://127.0.0.1:8050/ in your browser to display the precomputed network whose id is stored `cached_network_id.txt` (how to compute and cache new networks is dicussed later.
3. The network is visualized but none of the people nodes are labeled. Run a an image search on the upper-left corner of the screen for a photo category of interest such as "soldier", "guns", "confederate flag" or "[man in cowboy hat](https://www.bellingcat.com/news/2022/08/05/tracking-the-faceless-killers-who-mutilated-and-executed-a-ukrainian-pow/)".
4. The nodes with match photographs are now filled in with those photos.
5. Use the mouse to drag the network and zoom into the network cluster of interest.
6. Click any node to display the associated person's name, photograph, and social media profile link.

## Additional Information
This section includes any additional information that you want to mention about the tool, including:
- Potential next steps for the tool (i.e. what you would implement if you had more time)
- Any limitations of the current implementation of the tool
- Motivation for design/architecture decisions
