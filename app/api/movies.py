import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from pydantic import HttpUrl
from sqlalchemy.orm import Session

from app.models import Movie, SearchParams
from app.scrapers.yts import browse_yts, search_movie, get_movie_by_url
from app.database.models import MovieCache
from app.database.session import get_db

router = APIRouter()


@router.get("/search", response_model=List[Movie], summary="Search movies by title")
async def search_movies(title: str = Query(..., description="Movie title to search for")):
    """
    Search for movies by title.
    
    Returns a list of movies matching the search query.
    
    ###Search for a movie
    ```bash
    curl -X GET "http://localhost:8000/api/v1/movies/search?title=matrix"
    ```
    """
    movies = await search_movie(title)
    return movies


@router.post("/browse", response_model=List[Movie], summary="Browse movies with filters")
async def browse_movies(params: SearchParams, db: Session = Depends(get_db)):
    """
    Browse movies with various filters.
    
    - **keyword**: Search term
    - **quality**: Filter by quality (all, 720p, 1080p, 2160p)
    - **genre**: Filter by genre
    - **rating**: Minimum IMDB rating
    - **year**: Filter by year
    - **order_by**: Sort order (featured, date, seeds, peers, etc.)
    - **page**: Page number
    """
    movies = await browse_yts(params)
    # for movie in movies:
    #     movie_orm = MovieCache(
    #         title=movie.title,
    #         year=movie.year,
    #         rating=movie.rating,
    #         link=str(movie.link),
    #         genre=movie.genre,
    #         img=str(movie.img),
    #         description=movie.description,
    #         torrents_json=[{k: str(v) for k,v in t.model_dump().items()} for t in movie.torrents],
    #         expires_at=datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)
    #     )
    #     movie_orm.save(db)
    return movies


@router.get("/movie", response_model=Movie, summary="Get movie details by URL")
async def get_movie(url: HttpUrl):
    """
    Get detailed information about a specific movie by its URL.
    """
    movie = await get_movie_by_url(str(url))
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return movie


@router.get("/latest", response_model=List[Movie], summary="Get latest movies")
async def get_latest(
    limit: int = Query(10, ge=1, le=50, description="Number of movies to return"),
    quality: Optional[str] = Query(None, description="Filter by quality")
):
    """
    Get the latest movies added to YTS.
    
    - **limit**: Number of movies to return (default: 10, max: 50)
    - **quality**: Optional filter by quality (720p, 1080p, 2160p)
    """
    params = SearchParams(
        order_by="date",
        quality=quality or "all"
    )
    
    movies = await browse_yts(params)
    return movies[:limit]


@router.get("/top", response_model=List[Movie], summary="Get top rated movies")
async def get_top_rated(
    limit: int = Query(10, ge=1, le=50, description="Number of movies to return"),
    quality: Optional[str] = Query(None, description="Filter by quality"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    year: Optional[int] = Query(None, description="Filter by year")
):
    """
    Get top rated movies.
    
    - **limit**: Number of movies to return (default: 10, max: 50)
    - **quality**: Optional filter by quality (720p, 1080p, 2160p)
    - **genre**: Optional filter by genre
    - **year**: Optional filter by year
    """
    params = SearchParams(
        order_by="rating",
        quality=quality or "all",
        genre=genre or "all",
        year=year
    )
    
    movies = await browse_yts(params)
    return movies[:limit]