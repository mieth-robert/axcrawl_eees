import os
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import datetime
import openai

# Replace with your OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

def fetch_arxiv_eess_new():
    # Define the URL for ArXiv eess new submissions
    url = "https://arxiv.org/list/eess/new"
    
    # Fetch the content of the webpage
    response = requests.get(url)
    if response.status_code != 200:
        print("Failed to retrieve the webpage:", response.status_code)
        return None
    
    # Parse the webpage content
    soup = BeautifulSoup(response.content, "html.parser")
    
    # Find the sections containing the titles and abstracts
    titles = soup.find_all("div", class_="list-title mathjax")
    authors = soup.find_all("div", class_="list-authors")
    abstracts = soup.find_all("p", class_="mathjax")

    # Extract and store information
    papers = []
    for i in range(len(titles)):
        title = titles[i].text.replace("Title:", "").replace("\n", "").strip()
        author_list = authors[i].text.strip().replace("Authors:\n", "").replace("\n", ", ")
        abstract = abstracts[i].text.strip().replace("△ Less\n", "").replace("\n", " ")
        
        papers.append({
            "title": title,
            "authors": author_list,
            "abstract": abstract
        })
    
    return papers

def load_selection_prompt(filename):
    with open(filename, "r") as file:
        return file.read().strip()
    
def load_selection_prompt(filename):
    with open(filename, "r") as file:
        return file.read().strip()

def check_paper_with_gpt(paper, selection_prompt):
    query = f"""
    Selection criteria:
    {selection_prompt}

    Paper details:
    Title: {paper['title']}
    Authors: {paper['authors']}
    Abstract: {paper['abstract']}

    Does this paper match the selection criteria? Answer 'Yes' or 'No' only.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that evaluates whether a paper matches a selection criteria."},
                {"role": "user", "content": query}
            ],
            temperature=0,
            max_tokens=10
        )
        answer = response.choices[0].message.content.strip()
        return answer.lower() == "yes"
    except Exception as e:
        print(f"Error querying OpenAI API: {e}")
        return False
    
def get_relevant_papers_with_gpt(papers, selection_prompt):
    # Create a combined query with all papers
    papers_text = "\n\n".join([
        f"Paper {i+1}:\nTitle: {paper['title']}\nAuthors: {paper['authors']}\nAbstract: {paper['abstract']}"
        for i, paper in enumerate(papers)
    ])
    
    query = f"""
    Selection criteria:
    {selection_prompt}

    Below is a list of papers. For each paper, indicate if it matches the criteria. Respond with a list of the numbers of the matching papers. Only write the numbers separated by commas.

    {papers_text}
    """
    
    try:
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that evaluates papers based on selection criteria."},
                {"role": "user", "content": query}
            ],
            temperature=0,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error querying OpenAI API: {e}")
        return None
    
def save_relevant_papers_to_file(papers, relevant_indices, path="queries/"):
    # Get the current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"{path}arxiv_eess_{current_date}.txt"

    # Extract relevant papers and format them
    formatted_papers = []
    for idx in relevant_indices:
        paper = papers[idx]
        formatted_papers.append(
            f"Title: {paper['title']}\n"
            f"Authors: {paper['authors']}\n"
            f"Abstract: {paper['abstract']}\n"
            "------------------------------"
        )

    # Combine into a single string
    file_content = "\n\n".join(formatted_papers)

    # Save to file
    with open(filename, "w") as file:
        file.write(file_content)

    print(f"Relevant papers saved to {filename}.")

def save_relevant_papers_to_html(papers, relevant_indices):
    # Get the current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"html/arxiv_eess_{current_date}.html"

    # Start building the HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Arxiv eess Papers</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
            .paper {{ margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }}
            h2 {{ margin: 0 0 5px; font-size: 1.4em; }}
            p {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
    <h1>Relevant ArXiv eess Papers - {current_date}</h1>
    """

    # Add each relevant paper to the HTML
    for idx in relevant_indices:
        paper = papers[idx]
        html_content += f"""
        <div class="paper">
            <h2>{paper['title']}</h2>
            <p><strong>Authors:</strong> {paper['authors']}</p>
            <p>{paper['abstract']}</p>
        </div>
        """

    # Close the HTML content
    html_content += """
    </body>
    </html>
    """

    # Save to an HTML file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(html_content)

    print(f"Relevant papers saved to {filename}.")

def save_relevant_papers_to_html_amend(papers, relevant_indices):
    # Get the current date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    filename = f"arxiv_eess.html"

    # Load existing HTML file if it exists
    try:
        with open(filename, "r", encoding="utf-8") as file:
            existing_html = file.read()
    except FileNotFoundError:
        existing_html = None

    # Start building the new HTML content
    new_html_content = f"""
    <div class="paper">
        <h2>Relevant ArXiv eess Papers - {current_date}</h2>
    </div>
    """

    for idx in relevant_indices:
        paper = papers[idx]
        new_html_content += f"""
        <div class="paper">
            <h2>{paper['title']}</h2>
            <p><strong>Authors:</strong> {paper['authors']}</p>
            <p>{paper['abstract']}</p>
        </div>
        """

    # If file exists, extract old entries and merge
    if existing_html:
        # Extract old papers
        start_tag = "<body>"
        end_tag = "</body>"
        body_start = existing_html.find(start_tag) + len(start_tag)
        body_end = existing_html.find(end_tag)
        old_content = existing_html[body_start:body_end].strip()

        # Combine new and old content
        combined_content = new_html_content + old_content

        # Limit to the 500 most recent entries
        combined_papers = combined_content.split('<div class="paper">')
        if len(combined_papers) > 501:  # Include the header
            combined_papers = combined_papers[:501]

        final_body_content = "<div class=\"paper\">".join(combined_papers)
    else:
        # If no existing file, use only new content
        final_body_content = new_html_content

    # Finalize HTML
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Arxiv eess Papers</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
            .paper {{ margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #ccc; }}
            h2 {{ margin: 0 0 5px; font-size: 1.4em; }}
            p {{ margin: 5px 0; }}
        </style>
    </head>
    <body>
    {final_body_content}
    </body>
    </html>
    """

    # Save to an HTML file
    with open(filename, "w", encoding="utf-8") as file:
        file.write(final_html)

    print(f"Relevant papers saved to {filename}.")

def main():
    print("Fetching ArXiv eess new submissions...")
    papers = fetch_arxiv_eess_new()
    if not papers:
        print("No papers were fetched.")
        return
    print(f"{len(papers)} papers were fetched.")

    print("Loading selection criteria...")
    selection_prompt = load_selection_prompt("selection_request.txt")

    print("Querying ChatGPT for relevant papers...")
    relevant_papers = get_relevant_papers_with_gpt(papers, selection_prompt)
    relevant_papers_list = [int(paper_num)-1 for paper_num in relevant_papers.split(",")]
    
    print(relevant_papers_list)

    print(f"\nFound {len(relevant_papers_list)} matching papers.")
    for i in relevant_papers_list:
        paper = papers[i]
        print(f"\nPaper {i}:")
        print(f"Title: {paper['title']}")
        print(f"Authors: {paper['authors']}")
        print(f"Abstract: {paper['abstract']}")

    print("Saving to file.")
    save_relevant_papers_to_file(papers, relevant_papers_list)
    save_relevant_papers_to_html_amend(papers, relevant_papers_list)

if __name__ == "__main__":
    main()
