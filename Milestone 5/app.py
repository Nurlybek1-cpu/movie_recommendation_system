from flask import Flask, render_template, request
import pandas as pd
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

app = Flask(__name__)

# Load and preprocess data
data = pd.read_csv('cleaned_I_THINK.csv')
data['genres'] = data['genres'].apply(eval)  # Convert genres to a list
data['genres_string'] = data['genres'].apply(lambda x: ", ".join(sorted(x)))
data['user_rating'] = pd.to_numeric(data['user_rating'], errors='coerce').fillna(0.0)

genres_list = ['Action', 'Adventure', 'Animation', 'Comedy', 'Crime', 'Documentary', 'Drama', 'Family',
               'Fantasy', 'History', 'Horror', 'Music', 'Mystery', 'Romance', 'Science Fiction', 'TV Movie',
               'Thriller', 'War', 'Western']

# Content-Based Filtering
def recommend_content_based(input_genres, top_n=10):
    input_genres_set = set(input_genres)

    # Calculate similarity using Jaccard index
    def genre_similarity(movie_genres):
        return len(input_genres_set.intersection(movie_genres)) / len(input_genres_set.union(movie_genres))

    data['similarity'] = data['genres'].apply(genre_similarity)
    recommendations = data.sort_values(by='similarity', ascending=False).head(top_n)
    return recommendations[['title', 'genres_string', 'user_rating']].to_dict('records')

# Collaborative Filtering
def collaborative_filtering(top_n=10):
    # Create a user-item matrix (dummy user_id)
    user_item_matrix = pd.pivot_table(data, values='user_rating', index='title', columns='release_year', fill_value=0)

    # Normalize the matrix
    scaler = StandardScaler()
    user_item_matrix_scaled = scaler.fit_transform(user_item_matrix)

    # Apply SVD
    svd = TruncatedSVD(n_components=20, random_state=42)
    matrix_svd = svd.fit_transform(user_item_matrix_scaled)

    # Train a Nearest Neighbors model
    model_knn = NearestNeighbors(metric='cosine', algorithm='brute')
    model_knn.fit(matrix_svd)

    # Recommend movies for a random title
    movie_indices = np.random.choice(user_item_matrix.index, size=1)
    movie_idx = user_item_matrix.index.get_loc(movie_indices[0])
    distances, indices = model_knn.kneighbors([matrix_svd[movie_idx]], n_neighbors=top_n+1)

    recommendations = [{'title': user_item_matrix.index[i]} for i in indices.flatten()[1:]]
    return recommendations, movie_indices[0]

# Filter movies
def filter_movies(search_title, selected_genres, all_genres, sort_rating, only_released, top_n=20):
    filtered = data

    # Filter by title
    if search_title:
        filtered = filtered[filtered['title'].str.contains(search_title, case=False, na=False)]
        if not filtered.empty:
            movie_genres = filtered.iloc[0]['genres']
            similar_movies = data[data['genres'].apply(lambda x: len(set(x) & set(movie_genres)) >= 3)]
            filtered = pd.concat([filtered, similar_movies]).drop_duplicates(subset=['title', 'release_year'])

    # Filter by genres
    if selected_genres:
        selected_genres_set = set(selected_genres)
        if all_genres:
            filtered = filtered[filtered['genres'].apply(lambda x: selected_genres_set.issubset(set(x)))]
        else:
            filtered = filtered[filtered['genres'].apply(lambda x: bool(set(x) & selected_genres_set))]

    if only_released:
        filtered = filtered[filtered['release_year'] <= 2024]

    if sort_rating:
        filtered = filtered.sort_values(by='user_rating', ascending=False)

    return filtered.head(top_n).to_dict('records')

# Routes
@app.route('/')
def home():
    return render_template('index.html', genres_list=genres_list)

@app.route('/filter', methods=['POST'])
def filter():
    search_title = request.form.get('search_title')
    selected_genres = request.form.getlist('selected_genres')
    all_genres = request.form.get('all_genres') == 'on'
    sort_rating = request.form.get('sort_rating') == 'on'
    only_released = request.form.get('only_released') == 'on'

    recommendations = filter_movies(search_title, selected_genres, all_genres, sort_rating, only_released)
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/content_based', methods=['POST'])
def content_based():
    selected_genres = request.form.getlist('selected_genres')
    recommendations = recommend_content_based(selected_genres, top_n=10)
    return render_template('recommendations.html', recommendations=recommendations)

@app.route('/collaborative', methods=['POST'])
def collaborative():
    recommendations, base_movie = collaborative_filtering(top_n=10)
    return render_template('recommendations.html', recommendations=recommendations, base_movie=base_movie)

if __name__ == "__main__":
    app.run(debug=True)
