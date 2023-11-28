from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup, Comment
import re

app = Flask(__name__)


def get_theme_info(theme_slug):
    # Use WordPress.org API to fetch theme information based on slug
    theme_info_url = f"https://api.wordpress.org/themes/info/1.1/?action=theme_information&request[slug]={theme_slug}"
    response = requests.get(theme_info_url)
    if response.status_code == 200:
        return response.json()  # Extract and return theme information
    return None

def get_plugin_info(plugin_slug):
    # Use WordPress.org API to fetch plugin information based on slug
    plugin_info_url = f"https://api.wordpress.org/plugins/info/1.1/?action=plugin_information&request[slug]={plugin_slug}"
    response = requests.get(plugin_info_url)
    if response.status_code == 200:
        return response.json()  # Extract and return plugin information
    return None

def get_website_info(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract WordPress version
            wordpress_version = soup.find('meta', {'name': 'generator'})
            wordpress_version = wordpress_version.get('content') if wordpress_version else None

            # Extract theme information
            theme_info = soup.find('link', {'rel': 'stylesheet'})
            theme_name = theme_info.get('href').split('/')[-2] if theme_info else None

            # Extract plugin information
            plugin_scripts = soup.find_all('script', src=re.compile(r'.*plugins.*\.js'))
            plugins = []
            for script in plugin_scripts:
                plugin = re.search(r'.*plugins/(.*?)/.*\.js', script.get('src'))
                if plugin:
                    plugin_name = plugin.group(1)
                    if plugin_name not in plugins:  # Check for duplicates before appending
                        plugins.append(plugin_name)

            # Initialize libraries info
            libraries_info = {
                'jQuery': None,
                'Bootstrap': None,
                'Bulma': None,
                'Foundation': None,
                'Tailwind': None
            }

            # Extract JavaScript libraries
            js_libraries = soup.find_all('script', src=True)
            for js in js_libraries:
                js_src = js['src'].lower()
                if 'jquery' in js_src:
                    match = re.search(r'version/(\d+\.\d+\.\d+)', js_src)
                    libraries_info['jQuery'] = match.group(1) if match else None
                elif 'bootstrap' in js_src:
                    match = re.search(r'bootstrap/(\d+\.\d+\.\d+)', js_src)
                    libraries_info['Bootstrap'] = match.group(1) if match else None
                elif 'bulma' in js_src:
                    match = re.search(r'bulma/(\d+\.\d+\.\d+)', js_src)
                    libraries_info['Bulma'] = match.group(1) if match else None
                elif 'foundation' in js_src:
                    match = re.search(r'foundation/(\d+\.\d+\.\d+)', js_src)
                    libraries_info['Foundation'] = match.group(1) if match else None
                elif 'tailwind' in js_src:
                    match = re.search(r'tailwindcss/(\d+\.\d+\.\d+)', js_src)
                    libraries_info['Tailwind'] = match.group(1) if match else None

            # Collect all the information
            website_info = {
                'WordPress Version': wordpress_version,
                'Theme Name': theme_name,
                'Plugins': plugins,
                'Libraries Info': libraries_info
            }
            # Remove duplicate plugins
            if website_info and 'Plugins' in website_info:
                website_info['Plugins'] = list(set(website_info['Plugins']))

            return website_info

        else:
            print("Failed to retrieve the URL. Status code:", response.status_code)
            return None

    except Exception as e:
        print("An error occurred:", e)
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        result = get_website_info(url)
        if result:
            theme_info = None
            plugin_info = {}

            if result['Theme Name']:
                theme_info = get_theme_info(result['Theme Name'].lower())

            if result['Plugins']:
                for plugin in result['Plugins']:
                    plugin_data = get_plugin_info(plugin.lower())
                    plugin_info[plugin] = plugin_data if plugin_data else None
            return render_template('index.html', result=result, theme_info=theme_info, plugin_info=plugin_info)

    return render_template('index.html', result=None, error=False)

if __name__ == '__main__':
    app.run(debug=True)



