"""
Need to save state to local file in order to resume interupted download.
links structure:
-href
-level  (0 is home)
-parent link
-status (0=scanned | 1=downloaded)
"""

import requests
from bs4 import BeautifulSoup
from os.path import isfile, isdir
from os import makedirs, mkdir

class Page:
    def __init__(self, root_url:str, url:str='', level:int=0, links=[], checked_links=[], destination=None):
        # Root url used for concatenate base url + sub url
        # ie. https://example.com/ + dir/
        self.root_url = root_url
        self.url = url
        self.level = level
        self.content = None
        self.links = links
        self.checked_links = checked_links
        if destination:
            self.destination = destination
        else:
            self.destination = url
        if not isdir(self.destination):
            mkdir(self.destination)
        self.static = []
        # print("Searching in level:", self.level)
        self.getContent()
        self.getLinks()
        self.getStatic()
        self.writeContent()
        self.saveStatic()
        self.checked_links.append(self.url)

        # Recursive method: get sub pages
        for link in self.links:
            if link not in self.checked_links:
                Page(root_url=self.root_url, 
                url=link, 
                level=self.level+1, 
                links=self.links,
                checked_links=self.checked_links,
                destination=self.destination)

    def getContent(self):
        """This will make request and collect page content."""
        fullpath = self.root_url + self.url
        print("Requesting:", fullpath)
        source  = requests.get(fullpath).text
        self.content = BeautifulSoup(source, 'lxml')
        return self.content
    
    def filterLink(self, href):
        print("Checking link:", href)
        """Filter links to reduce redundancy."""
        # exclude id from links
        if '#' in href:
            href = href.split('#')[0]

        """This will make sure only internal links will remain."""
        if 'http' in href or 'https' in href:
            # Cut the root part in absolute url.
            if href.startswith(self.url):
                href = href[len(self.url)-1:]
            else:
                return False
        return href
    
    def getLinks(self):
        """Search all anchor tag excluding '#'. 
        """
        for link in self.content.find_all('a'):
            href = link.attrs['href']
            # Skip Current page
            if href != '#':
                href = self.filterLink(href)
                if href:
                    # Include only unique links
                    if href not in self.links:
                        self.links.append(href)
        print("Found", len(self.links), "links in", self.url)
        return self.links
    
    def getStatic(self):
        """Collect all unique CSS and JS files"""
        # CSS
        for file in self.content.find_all('link'):
            href = file.attrs['href']
            href = self.filterLink(href)
            if href:
                # link tag can also contain html files
                # Include only unique links
                if href not in self.static and href not in self.links:
                    self.static.append(href)
        # JS
        for file in self.content.find_all('script'):
            if 'src' in file.attrs:
                href = file.attrs['src']
                href = self.filterLink(href)
                if href:
                    # Include only unique scripts
                    if href not in self.static:
                        self.static.append(href)
        print("Found", len(self.static), "static files in", self.url)
        return self.static
    
    def writeContent(self):
        content = self.content.prettify()
        content.replace(self.root_url, '')
        
        # check file ext if have
        path_ = self.url.split('.')
        ext = path_[-1]
        if ext == 'html' or ext == 'php':
            ext = '.html'
            path = ".".join(path_[:-1]) + ext
        else:
            filename = 'index.html'
            path = self.url + filename
        if self.level == 0:
            path = 'index.html'
        print("Test path:", path)
        fullpath = self.destination + "/" + path
        tmp_path = "/".join(fullpath.split('/')[:-1])
        if not isdir(tmp_path):
            makedirs(tmp_path)
        if not isfile(fullpath):
            print("Writing file:", fullpath)
            with open(fullpath, 'w+', encoding='utf-8') as f:
                f.write(content)
    
    def saveStatic(self):
        # Write static files
        for file in self.static:
            # Create directories
            dirs = file.split('/')
            if len(dirs) > 1:
                dirs = dirs[:-1]
                dirs.insert(0,self.destination)
                makedirs("/".join(dirs), exist_ok=True)

            content  = requests.get(self.root_url + self.url + file).text
            fullpath = self.destination + "/" + file
            if not isfile(fullpath):
                print("Saving:", fullpath)
                with open(fullpath, 'w+') as f:
                    f.write(content)

if __name__ == "__main__":
    project_name = "PyQt6"
    Page('https://www.riverbankcomputing.com/static/Docs/PyQt6/', destination=project_name)
