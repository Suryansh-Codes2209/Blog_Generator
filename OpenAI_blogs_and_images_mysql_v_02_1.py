# NOTES FOR THE DEVELOPER:
# Update API_KEY and ORG_ID values for your organization. They can be extracted from: 
#       ORG_ID  => https://beta.openai.com/account/org-settings
#       API_KEY => https://beta.openai.com/account/api-keys
# to customize product keywords: change "product_keywords" list
# to customize blog's content length: increase/decrease "max_tokens" variable however it has a max quota
# changing the "temperature" parameter from 0 to 1 allows you to adjust the degree of "creativity" of the model
# to customize generated image sizes: modify "size" value in "image_response" request parameters.
# AI Image size value must be one of 256x256, 512x512, or 1024x1024


import openai
import pymysql
import configparser
import pandas
import requests
import math


config = configparser.ConfigParser()
config.read('config.ini')

host = config['DATABASE OUTPUT']['host']
name = config['DATABASE OUTPUT']['name']
password = config['DATABASE OUTPUT']['password']
database = config['DATABASE OUTPUT']['database']
table_name = config['DATABASE OUTPUT']['table_name']
file = pandas.read_excel(config['FILE PATH']['file_name']).values.tolist()


con = pymysql.connect(host=host,user=name,password=password,database=database)
#openai.organization = config['SETTINGS']['ORG_ID']
openai.api_key = config['SETTINGS']['API_KEY']
openai.Model.list()

blogs_dictionary = []

# the following products list is highly customizable
cur = con.cursor()
# Create table if not exist
cur.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
                id INTEGER NOT NULL PRIMARY KEY AUTO_INCREMENT,
                blog_title TEXT,
                blog_content TEXT,
                blog_image TEXT);""")
for row in file:
    temperat = row[3]
    max_length = row[2]
    what_need = row[1]
    
    try:
        if math.isnan(float(row[4])):
            image_enable = 0  # Set a default value or handle it appropriately
        else:
            image_enable = int(row[4])
    except ValueError:
        # Handle the case where row[3] is not a valid number
        image_enable = 0
    
    

    if isinstance(row[0], str):
        product_keywords = [x.strip() for x in row[0].split(',')]
    else:
        # Handle the case where row[0] is not a string
        product_keywords = []



    for prompt in product_keywords:
        # Create AI generated Blog from prompt
        blog_response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=f"{what_need} {prompt.strip()}",
            max_tokens=int(max_length),
            temperature=float(temperat),
        )
        blog_content = blog_response["choices"][0]["text"].strip()

        # Create AI generated image from prompt
        image_url = None
        if image_enable == 1:
            image_response = openai.Image.create(
                prompt=f"A {prompt}",
                n=1,
                size="256x256"
            )
            
            image_url = image_response["data"][0]["url"]
            with open(f'{prompt.strip()}.jpeg', 'wb') as f:
                f.write(requests.get(image_url).content)
        
        blogs_dictionary.append({
            'blog_title': prompt.strip(),
            'blog_content': blog_content.strip(),
            'blog_image': image_url,
             'task':what_need
        })

        cur.execute(f"INSERT INTO {table_name} (id, blog_title, blog_content, blog_image) VALUES (NULL, %s, %s, %s);",
                    (prompt.strip(), blog_content.strip(), image_url))
        con.commit()

pandas.DataFrame(blogs_dictionary).to_excel('give_full_path_for_output_file** not-give-relative-path')
con.close()

print("\n" + "*" * 20)
print("Successfully Executed _> !")
print("*" * 20 + "\n")

