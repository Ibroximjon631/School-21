import pytest
import os
import sys
from movielens_analysis import Movies, Ratings, Tags, Links, MovieLensAnalyzer

class TestMovies:
    def setup_method(self):
        self.movies = Movies("data/movies.csv")
    
    def test_get_movies_return_type(self):
        """Test if get_movies returns correct data type"""
        result = self.movies.get_movies()
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)
    
    def test_get_movie_by_id(self):
        """Test getting movie by ID"""
        movies = self.movies.get_movies()
        if movies:
            movie_id = movies[0]['movieId']
            result = self.movies.get_movie_by_id(movie_id)
            assert isinstance(result, dict)
            assert result['movieId'] == movie_id
    
    def test_get_movies_by_genre(self):
        """Test getting movies by genre"""
        result = self.movies.get_movies_by_genre('Drama')
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)
            assert 'Drama' in result[0]['genres']
    
    def test_get_all_genres(self):
        """Test getting all genres"""
        result = self.movies.get_all_genres()
        assert isinstance(result, list)
        assert all(isinstance(genre, str) for genre in result)
    
    def test_get_movies_count_by_genre(self):
        """Test movie count by genre"""
        result = self.movies.get_movies_count_by_genre()
        assert isinstance(result, dict)
        assert all(isinstance(key, str) and isinstance(value, int) for key, value in result.items())


class TestRatings:
    def setup_method(self):
        self.ratings = Ratings("data/ratings.csv")
    
    def test_get_ratings_return_type(self):
        """Test if get_ratings returns correct data type"""
        result = self.ratings.get_ratings()
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)
    
    def test_get_ratings_by_user(self):
        """Test getting ratings by user"""
        ratings = self.ratings.get_ratings()
        if ratings:
            user_id = ratings[0]['userId']
            result = self.ratings.get_ratings_by_user(user_id)
            assert isinstance(result, list)
            if result:
                assert all(r['userId'] == user_id for r in result)
    
    def test_get_ratings_by_movie(self):
        """Test getting ratings by movie"""
        ratings = self.ratings.get_ratings()
        if ratings:
            movie_id = ratings[0]['movieId']
            result = self.ratings.get_ratings_by_movie(movie_id)
            assert isinstance(result, list)
            if result:
                assert all(r['movieId'] == movie_id for r in result)
    
    def test_get_average_rating_by_movie(self):
        """Test average rating calculation"""
        ratings = self.ratings.get_ratings()
        if ratings:
            movie_id = ratings[0]['movieId']
            result = self.ratings.get_average_rating_by_movie(movie_id)
            assert isinstance(result, float)
            assert 0 <= result <= 5
    
    def test_get_top_rated_movies(self):
        """Test top rated movies"""
        result = self.ratings.get_top_rated_movies(5)
        assert isinstance(result, list)
        if len(result) > 1:
            assert result[0]['average_rating'] >= result[1]['average_rating']
    
    def test_get_rating_distribution(self):
        """Test rating distribution"""
        result = self.ratings.get_rating_distribution()
        assert isinstance(result, dict)
        assert all(isinstance(key, float) and isinstance(value, int) for key, value in result.items())


class TestTags:
    def setup_method(self):
        self.tags = Tags("data/tags.csv")
    
    def test_get_tags_return_type(self):
        """Test if get_tags returns correct data type"""
        result = self.tags.get_tags()
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)
    
    def test_get_tags_by_movie(self):
        """Test getting tags by movie"""
        tags = self.tags.get_tags()
        if tags:
            movie_id = tags[0]['movieId']
            result = self.tags.get_tags_by_movie(movie_id)
            assert isinstance(result, list)
            if result:
                assert all(t['movieId'] == movie_id for t in result)
    
    def test_get_most_popular_tags(self):
        """Test most popular tags"""
        result = self.tags.get_most_popular_tags(5)
        assert isinstance(result, list)
        # Check if sorted correctly
        if len(result) > 1:
            assert result[0]['count'] >= result[1]['count']


class TestLinks:
    def setup_method(self):
        self.links = Links("data/links.csv")
    
    def test_get_links_return_type(self):
        """Test if get_links returns correct data type"""
        result = self.links.get_links()
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)
    
    def test_get_link_by_movie_id(self):
        """Test getting link by movie ID"""
        links = self.links.get_links()
        if links:
            movie_id = links[0]['movieId']
            result = self.links.get_link_by_movie_id(movie_id)
            assert isinstance(result, dict) or result is None


class TestMovieLensAnalyzer:
    def setup_method(self):
        self.analyzer = MovieLensAnalyzer("data")
    
    def test_get_movie_stats(self):
        """Test movie statistics"""
        movies = self.analyzer.movies.get_movies()
        if movies:
            movie_id = movies[0]['movieId']
            result = self.analyzer.get_movie_stats(movie_id)
            assert isinstance(result, dict)
            assert 'movie' in result
            assert 'average_rating' in result
    
    def test_get_genre_analysis(self):
        """Test genre analysis"""
        result = self.analyzer.get_genre_analysis()
        assert isinstance(result, dict)
        if result:
            genre = list(result.keys())[0]
            assert 'movie_count' in result[genre]
            assert 'average_rating' in result[genre]
    
    def test_get_user_activity(self):
        """Test user activity analysis"""
        result = self.analyzer.get_user_activity()
        assert isinstance(result, dict)
        expected_keys = ['total_users', 'users_with_tags', 'average_ratings_per_user', 'average_tags_per_user']
        for key in expected_keys:
            assert key in result


if __name__ == '__main__':
    pytest.main([__file__, "-v"])