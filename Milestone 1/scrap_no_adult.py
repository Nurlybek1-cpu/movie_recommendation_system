import requests, csv

API = '4ca6db56909dbf602a88a278a634cdf0'
web = 'https://api.themoviedb.org/3/'
search = f"{web}discover/movie"
movies = f"{web}movie/"

we_need = [
    'title', 'genres', 'release_year', 'user_rating', "adult"
    'keywords', 'director', 'description', 'poster_url', 'trailer_url']

def fetch_url(url, params=None):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Failed: {e}")
        return None

def get_genres(genre_objects):
    return [genre['name'] for genre in genre_objects]

def fetch_movie_details(movie_id):
    details_url = f"{movies}{movie_id}?api_key={API}&language=en-US"
    credits_url = f"{movies}{movie_id}/credits?api_key={API}"
    keywords_url = f"{movies}{movie_id}/keywords?api_key={API}"
    trailers_url = f"{movies}{movie_id}/videos?api_key={API}"

    details = fetch_url(details_url)
    credits = fetch_url(credits_url)
    keywords = fetch_url(keywords_url)
    trailers = fetch_url(trailers_url)

    if not details:
        return None

    # try not to add adult
    if details.get('adult', False):
        return None

    title = details.get('title', '')
    genres = get_genres(details.get('genres', []))
    release_year = details.get('release_date', '').split('-')[0]
    user_rating = details.get('vote_average', 0.0)
    description = details.get('overview', '')
    poster_url = f"https://image.tmdb.org/t/p/w500{details.get('poster_path', '')}" if details.get('poster_path') else ''

    keywords = [keyword['name'] for keyword in keywords.get('keywords', [])] if keywords else []

    director = ''
    if credits:
        for crew_member in credits.get('crew', []):
            if crew_member.get('job') == 'Director':
                director = crew_member.get('name')
                break

    trailer_url = ''
    if trailers:
        for video in trailers.get('results', []):
            if video.get('type') == 'Trailer' and video.get('site') == 'YouTube':
                trailer_url = f"https://www.youtube.com/watch?v={video.get('key')}"
                break

    return [
        title, ', '.join(genres), release_year, user_rating,
        ', '.join(keywords), director, description, poster_url, trailer_url
    ]

def fetch_movies_data():
    movies_data = []
    page = 1

    while len(movies_data) < 5000:
        print(f"Fetching page {page}...")
        params = {
            'api_key': API,
            'language': 'en-US',
            'sort_by': 'popularity.desc',
            'page': page
        }
        response = fetch_url(search, params=params)

        if not response:
            print(f"Failed to fetch data for page {page}. Skipping...")
            page += 1
            continue

        for movie in response.get('results', []):
            movie_id = movie.get('id')
            if movie_id:
                movie_data = fetch_movie_details(movie_id)
                if movie_data:
                    movies_data.append(movie_data)

        page += 1

    return movies_data[:5000]

def save_to_csv(data, file_name='movies_data.csv'):
    try:
        with open(file_name, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(we_need)
            writer.writerows(data)
        print(f"Data successfully saved to {file_name}")
    except IOError as e:
        print(f"Error saving to file: {e}")

# Main Execution
def main():
    print("searching...")
    data = fetch_movies_data()
    print("saved")
    save_to_csv(data)

if __name__ == '__main__':
    main()
