from urllib.parse import urlparse, urlsplit, urlunsplit
from urllib.error import URLError
import logging
import tldextract
import requests
import sys
import re
import os

links_not_to_parse = ("#", "javascript", "?", "\"")
links_not_to_follow = ("mailto", "tel")
permanent_links = ("http", "https")

def check_and_fix_link(base, link):
    global links_not_to_parse
    global links_not_to_follow
    global permanent_links
    new_link = ""
    link_type = "ordinary"

    if (link[0] == "”" and link[-1] == "”"):  # some strange not utf-8 charachter (Qoutes I found in some links)
        link = link[1:-1]

    if link.startswith(links_not_to_parse):
        new_link = None
        link_type = "ignore"

    elif link.startswith(links_not_to_follow):
        new_link = link
        link_type = "not_to_folow"

    elif link.startswith(permanent_links):
        new_link = link

    elif link.startswith('/'):
        new_link = urlparse(base).netloc + link

    elif "#" in link:
        link = link[:link.index('#')]
        parsed_base = urlparse(base)
        parsed_scheme = parsed_base.scheme
        parsed_domain = parsed_base.netloc
        parsed_path = parsed_base.path
        try:
            if parsed_path.index(link) != -1:
                new_link = f"{parsed_scheme}://{parsed_domain}{parsed_path}"
        except ValueError as e:
            new_link = f"{base.rsplit('/', 1)[0]}/{link}"

    else:
        cuted_link = link[:link.index('.')] if "." in link else ""
        if base.endswith("/") and cuted_link in base:
            new_link = f"{base.rsplit('/', 2)[0]}/{link}"
        elif base.endswith("/"):
            new_link = f"{base.rsplit('/', 2)[0]}/{link}"
        elif "." in base.rsplit('/', 1)[1]:
            new_link = f"{base.rsplit('/', 1)[0]}/{link}"
        elif "#" in base:
            new_link = f"{base.rsplit('#', 1)[0]}{link}"
        else:
            new_link = f"{base}/{link}"

        # if (new_link == "https://www.guardicore.com/infectionmonkey/debian.html" or
        #     new_link == "https://www.guardicore.com/faq.html" or
        #     new_link =="https://www.guardicore.com/breach-and-attack-scenarios" or
        #     new_link == "breach-and-attack-scenarios.html" or
        #     new_link == "https://www.guardicore.com/checksums.html" or
        #     new_link == "https://www.guardicore.com/faq.html" or
        #     new_link == "https://www.guardicore.com/infectionmonkey/win.html"):
        #
        #     logging.warning(f"1||| LINK: {link} ||| BASE: {base}")
        #     logging.warning(f"1||| BASERSPLIT: {base.rsplit('/', 1)[0]}/{link} ")

    if new_link is not None and "../" in new_link:
            new_link = clean_link(new_link)

    return (link_type, str(new_link).lower())

def clean_link(link):
    parts = list(urlsplit(link))
    parts[2] = resolve_url_path(parts[2])
    return urlunsplit(parts)

def resolve_url_path(path):
    segments = path.split('/')
    segments = [segment + '/' for segment in segments[:-1]] + [segments[-1]]
    resolved = []
    for segment in segments:
        if segment in ('../', '..'):
            if resolved[1:]:
                resolved.pop()
        elif segment not in ('./', '.'):
            resolved.append(segment)
    return ''.join(resolved)

def open_url(url_object):
    try:
        html = requests.get(url_object[1])
    except URLError as e:
        html = e
        logging.warning(f"Thread: {threading.get_ident()} Run into strange exception: {str(e)} "
                        f"url: {str(url_object[1])} !!!!!!!!!")
    except ValueError as e:
        html = e
        logging.warning(f"Thread: {threading.get_ident()} Run into strange exception: {str(e)} "
                        f"url: {str(url_object[1])} !!!!!!!!!")
    return html

def check_same_domain(target_tld, link, base):
    base_domain = urlparse(base).netloc
    link_domain = urlparse(link).netloc
    return True if (target_tld.match(link) and base_domain == link_domain) else False

def parse_targets_tld(domain):
    extracted = tldextract.extract(domain)
    return re.compile(f"https?:\/\/"
                        f"(.+?\.)?"
                        f"{extracted.domain}"
                        f"([A-Za-z0-9\-\._~:\?#\[\]@!$&'\(\)\*\+,;\=]*)?"
                        f"\.{extracted.suffix}"
                        f"(\/[A-Za-z0-9\-\._~:\/\?#\[\]@!$&'\(\)\*\+,;\=]*)?")

def write_output(output_file, valid_links, broken_links, valid_nf_links, valid_f_links):
    sorted_valid_links = {k: v for k, v in sorted(valid_links.items(), key=lambda item: item[1])}
    output_file.write("=====================\n")
    output_file.write("Ordinary valid links:\n")
    output_file.write("=====================\n")
    output_file.write("\n")
    for i, url_object in enumerate(sorted_valid_links.items()):
        output_file.write(f"{str(i + 1):<5}. Level: {str(url_object[1]):<2} link: {str(url_object[0])}\n")

    output_file.write("\n\n")

    sorted_valid_nf_links = {k: v for k, v in sorted(valid_nf_links.items(), key=lambda item: item[1])}
    output_file.write("=========================\n")
    output_file.write("Not followed valid links:\n")
    output_file.write("=========================\n")
    output_file.write("\n")
    for i, url_object in enumerate(sorted_valid_nf_links.items()):
        output_file.write(f"{str(i + 1):<5}. Level: {str(url_object[1]):<2} link: {str(url_object[0])}\n")

    output_file.write("\n\n")

    sorted_valid_f_links = {k: v for k, v in sorted(valid_f_links.items(), key=lambda item: item[1])}
    output_file.write("=================\n")
    output_file.write("Valid file links:\n")
    output_file.write("=================\n")
    output_file.write("\n")
    for i, url_object in enumerate(sorted_valid_f_links.items()):
        output_file.write(f"{str(i + 1):<5}. Level: {str(url_object[1]):<2} link: {str(url_object[0])}\n")

    output_file.write("\n\n")

    sorted_broken_links = {k: v for k, v in sorted(broken_links.items(), key=lambda item: item[1])}
    output_file.write("==========\n")
    output_file.write("Bad Links:\n")
    output_file.write("==========\n")
    output_file.write("\n")
    for i, url_object in enumerate(sorted_broken_links.items()):
        output_file.write(f"{str(i + 1):<5}. "
                          f"Level: {str(url_object[1][0]):<2} "
                          f"Error: [{str(url_object[1][1]):<3}] "
                          f"link: {str(url_object[0])}\n")

    output_file.close()

def create_results_file(filename):
    if filename is not None and filename != "":
        try:
            if (not os.path.isdir('./results')):
                os.mkdir("results")
            os.chdir("results")
            output_file = open(filename, 'w')
            return output_file
        except Exception as e:
            print("Creation of the file / directory failed!")
            print("Exception is: " + str(e))
            exit()
    else:
        return sys.stdout