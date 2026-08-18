import os
import csv
import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Any, Optional

class Movies:
    def __init__(self, movies_file: str = "data/movies.csv"):
        self.movies_file = movies_file
        self.movies = self._load_movies()
    
    def _load_movies(self) -> List[Dict[str, Any]]:
        """Load movies from CSV file"""
        movies = []
        try:
            with open(self.movies_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    movies.append({
                        'movieId': int(row['movieId']),
                        'title': row['title'],
                        'genres': row['genres'].split('|')
                    })
        except FileNotFoundError:
            print(f"Warning: {self.movies_file} not found")
        return movies
    
    def get_movies(self) -> List[Dict[str, Any]]:
        """Return all movies"""
        return self.movies
    
    def get_movie_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get movie by movieId"""
        for movie in self.movies:
            if movie['movieId'] == movie_id:
                return movie
        return None
    
    def get_movies_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Get movies by genre"""
        return [movie for movie in self.movies if genre in movie['genres']]
    
    def get_all_genres(self) -> List[str]:
        """Get all unique genres"""
        genres = set()
        for movie in self.movies:
            genres.update(movie['genres'])
        return sorted(list(genres))
    
    def get_movies_count_by_genre(self) -> Dict[str, int]:
        """Get count of movies by genre"""
        genre_count = Counter()
        for movie in self.movies:
            for genre in movie['genres']:
                genre_count[genre] += 1
        return dict(genre_count)


class Ratings:
    def __init__(self, ratings_file: str = "data/ratings.csv"):
        self.ratings_file = ratings_file
        self.ratings = self._load_ratings()
    
    def _load_ratings(self) -> List[Dict[str, Any]]:
        """Load ratings from CSV file"""
        ratings = []
        try:
            with open(self.ratings_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    ratings.append({
                        'userId': int(row['userId']),
                        'movieId': int(row['movieId']),
                        'rating': float(row['rating']),
                        'timestamp': int(row['timestamp'])
                    })
        except FileNotFoundError:
            print(f"Warning: {self.ratings_file} not found")
        return ratings
    
    def get_ratings(self) -> List[Dict[str, Any]]:
        """Return all ratings"""
        return self.ratings
    
    def get_ratings_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get ratings by user ID"""
        return [rating for rating in self.ratings if rating['userId'] == user_id]
    
    def get_ratings_by_movie(self, movie_id: int) -> List[Dict[str, Any]]:
        """Get ratings by movie ID"""
        return [rating for rating in self.ratings if rating['movieId'] == movie_id]
    
    def get_average_rating_by_movie(self, movie_id: int) -> float:
        """Get average rating for a movie"""
        movie_ratings = self.get_ratings_by_movie(movie_id)
        if not movie_ratings:
            return 0.0
        return sum(r['rating'] for r in movie_ratings) / len(movie_ratings)
    
    def get_top_rated_movies(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get top N rated movies (minimum 5 ratings)"""
        movie_ratings = defaultdict(list)
        for rating in self.ratings:
            movie_ratings[rating['movieId']].append(rating['rating'])
        
        avg_ratings = []
        for movie_id, ratings in movie_ratings.items():
            if len(ratings) >= 5: 
                avg_ratings.append({
                    'movieId': movie_id,
                    'average_rating': sum(ratings) / len(ratings),
                    'rating_count': len(ratings)
                })
        
        return sorted(avg_ratings, key=lambda x: x['average_rating'], reverse=True)[:n]
    
    def get_rating_distribution(self) -> Dict[float, int]:
        """Get distribution of ratings"""
        distribution = Counter()
        for rating in self.ratings:
            distribution[rating['rating']] += 1
        return dict(distribution)


class Tags:
    def __init__(self, tags_file: str = "data/tags.csv"):
        self.tags_file = tags_file
        self.tags = self._load_tags()
    
    def _load_tags(self) -> List[Dict[str, Any]]:
        """Load tags from CSV file"""
        tags = []
        try:
            with open(self.tags_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    tags.append({
                        'userId': int(row['userId']),
                        'movieId': int(row['movieId']),
                        'tag': row['tag'],
                        'timestamp': int(row['timestamp'])
                    })
        except FileNotFoundError:
            print(f"Warning: {self.tags_file} not found")
        return tags
    
    def get_tags(self) -> List[Dict[str, Any]]:
        """Return all tags"""
        return self.tags
    
    def get_tags_by_movie(self, movie_id: int) -> List[Dict[str, Any]]:
        """Get tags by movie ID"""
        return [tag for tag in self.tags if tag['movieId'] == movie_id]
    
    def get_tags_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Get tags by user ID"""
        return [tag for tag in self.tags if tag['userId'] == user_id]
    
    def get_most_popular_tags(self, n: int = 10) -> List[Dict[str, Any]]:
        """Get most popular tags"""
        tag_count = Counter(tag['tag'] for tag in self.tags)
        return [{'tag': tag, 'count': count} for tag, count in tag_count.most_common(n)]
    
    def get_tags_by_genre(self, movies_obj: Movies, genre: str) -> List[str]:
        """Get all tags for movies of a specific genre"""
        genre_movies = movies_obj.get_movies_by_genre(genre)
        genre_movie_ids = [movie['movieId'] for movie in genre_movies]
        
        tags = []
        for tag in self.tags:
            if tag['movieId'] in genre_movie_ids:
                tags.append(tag['tag'])
        return tags


class Links:
    def __init__(self, links_file: str = "data/links.csv"):
        self.links_file = links_file
        self.links = self._load_links()
    
    def _load_links(self) -> List[Dict[str, Any]]:
        """Load links from CSV file"""
        links = []
        try:
            with open(self.links_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    link_data = {
                        'movieId': int(row['movieId']),
                        'imdbId': row['imdbId'] if row['imdbId'] else None,
                        'tmdbId': row['tmdbId'] if row['tmdbId'] else None
                    }
                    links.append(link_data)
        except FileNotFoundError:
            print(f"Warning: {self.links_file} not found")
        return links
    
    def get_links(self) -> List[Dict[str, Any]]:
        """Return all links"""
        return self.links
    
    def get_link_by_movie_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        """Get links by movie ID"""
        for link in self.links:
            if link['movieId'] == movie_id:
                return link
        return None
    
    def get_movies_with_external_links(self) -> List[Dict[str, Any]]:
        """Get movies that have external links"""
        return [link for link in self.links if link['imdbId'] or link['tmdbId']]


class MovieLensAnalyzer:
    """Main analyzer class that combines all data sources"""
    
    def __init__(self, data_dir: str = "data"):
        self.movies = Movies(f"{data_dir}/movies.csv")
        self.ratings = Ratings(f"{data_dir}/ratings.csv")
        self.tags = Tags(f"{data_dir}/tags.csv")
        self.links = Links(f"{data_dir}/links.csv")
    
    def get_movie_stats(self, movie_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a movie"""
        movie = self.movies.get_movie_by_id(movie_id)
        if not movie:
            return {}
        
        movie_ratings = self.ratings.get_ratings_by_movie(movie_id)
        movie_tags = self.tags.get_tags_by_movie(movie_id)
        links = self.links.get_link_by_movie_id(movie_id)
        
        return {
            'movie': movie,
            'rating_count': len(movie_ratings),
            'average_rating': self.ratings.get_average_rating_by_movie(movie_id) if movie_ratings else 0,
            'tags': [tag['tag'] for tag in movie_tags],
            'external_links': links
        }
    
    def get_genre_analysis(self) -> Dict[str, Any]:
        """Analyze movies by genre"""
        genre_stats = {}
        for genre in self.movies.get_all_genres():
            genre_movies = self.movies.get_movies_by_genre(genre)
            genre_ratings = []
            
            for movie in genre_movies:
                ratings = self.ratings.get_ratings_by_movie(movie['movieId'])
                if ratings:
                    avg_rating = sum(r['rating'] for r in ratings) / len(ratings)
                    genre_ratings.append(avg_rating)
            
            genre_stats[genre] = {
                'movie_count': len(genre_movies),
                'average_rating': sum(genre_ratings) / len(genre_ratings) if genre_ratings else 0,
                'rating_count': len(genre_ratings)
            }
        
        return genre_stats
    
    def get_user_activity(self) -> Dict[str, Any]:
        """Analyze user activity"""
        user_ratings = defaultdict(list)
        user_tags = defaultdict(list)
        
        for rating in self.ratings.get_ratings():
            user_ratings[rating['userId']].append(rating)
        
        for tag in self.tags.get_tags():
            user_tags[tag['userId']].append(tag)
        
        active_users = {
            'total_users': len(user_ratings),
            'users_with_tags': len(user_tags),
            'average_ratings_per_user': len(self.ratings.get_ratings()) / len(user_ratings) if user_ratings else 0,
            'average_tags_per_user': len(self.tags.get_tags()) / len(user_tags) if user_tags else 0
        }
        
        return active_users


if __name__ == '__main__':
    analyzer = MovieLensAnalyzer()
    print("MovieLens Analysis Module Loaded Successfully!")
    print(f"Total Movies: {len(analyzer.movies.get_movies())}")
    print(f"Total Ratings: {len(analyzer.ratings.get_ratings())}")
    print(f"Total Tags: {len(analyzer.tags.get_tags())}")