# Python-Gelbooru
## An async (and soon sync) wrapper for the Gelbooru API

Everything starts with the `AsyncGelbooru` class. It can be used as a context manager.
Here's an example before showing the full docs

```py
import asyncio
from python_gelbooru import AsyncGelbooru

api_key, user_id = ("haha_not", "telling_you")
async def main():
    async with AsyncGelbooru(api_key=api_key,
                             user_id=user_id) as gel:
        yuyu = await gel.search_posts(['saigyouji yuyuko', 'rating:explicit'], limit=10, random=True)
       

        tasks = [i.async_download(f"./arts/{i.id}") for i in yuyu]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
```
This downloads 10 random arts with the tags `saigyouji_yuyuko` that are rated explicit to the `arts` folder and uses the id of the post for the file name (and automatically uses the correct extension)

## Classes
The documentation of all of the attributes, methods and properties of these classes can be found here, or in the docstrings.
- `AsyncGelbooru` - The base class used for interacting with Gelbooru asynchronously.
  The other classes should almost never be constructed except from one of this class's methods.
- `Post` - Represents a Gelbooru post.
- `Tag` - Represents a Gelbooru tag
- `Comment` - Represents a Gelbooru Comment

### AsyncGelbooru
Attributes
- `AsyncGelbooru.session: aiohttp.ClientSession`
    - The session this instance uses to fetch everything on Gelbooru. The constructor creates a new session every time the class is created, and not every time a function is called.

Methods
- `def __init__(self, *, api_key: Optional[str] = None, user_id: Optional[str] = None)`
    - If values are provided to the constructor, it will represent a session that has a verified API key and user id.

    - **Note:** Results will not be changed if the API key or user id is invalid, just that you might be more rate limited more often.

-  `async def search_posts(self, tags: Iterable[str], *, exclude_tags: Iterable[str] = None,
   limit=1, page_number: int = 0, random: bool = False
   ) -> Tuple[Post, ...]`
    - Searches Gelbooru with the tags and excluded tags provided.
      These tags are not `Tag` objects, but you can call `str()` on the `Tag` object to get the tag that goes in the iterable.

    - The strings that go in both of the `tags` and `exclude_tags` parameters can have spaces, improper capitalization. They will be properly formatted during search.
    - If `random` is True: returns random posts.
    - `page_number` is with respect to the limit.
    - Even though the Gelbooru API returns 100 posts by default when a limit isn't provided, this library returns 1 to save from some disasters.

-  `async def get_post(self, *, post_id: Optional[int] = None,
   md5: Optional[str] = None) -> Tuple[Post, ...]`
    - Grabs a post either by id or md5 hash.
        - The md5 hash is also the default file name for an image, so if you have a random image from Gelbooru, you can find its source.
    - Always returns a tuple. Almost always, these tuples contain a single element, or no elements if no matching posts can be found.
    - `post_id` and `md5` are mutually exclusive and passing both in will raise a `ValueError`, along with not passing either in.

- `async def get_post_comments(self, post: Post) -> Tuple[Comment, ...]`
    - Gets all comments on a post.

- `async def search_tags(self, names: Optional[Iterable[str]] = None, limit: int = 1, *,
  name_pattern: Optional[str] = None,
  after_id: Optional[int] = None,
  order: Optional[Literal['asc', 'desc']] = None,
  order_by: Optional[Literal['date', 'count', 'name']] = None) -> Tuple[Tag, ...]`
    - Search the Gelbooru Tag List for tags.
    - `names`: An `Iterable` of strings that contain the names of tags to get.
      Can contain spaces and improper capitalization, as that becomes fixed.
    - `limit`: The maximum amount of tags to return
    - `name_pattern`: A wildcard-based search for searching for tags. `_` represents a single character wildcard,
      and `%` represents a multi-character wildcard.
      DO NOT TRY TO USE REGEX. IT WILL NOT END WELL.
    - `after_id`: Returns only posts with an id greater than this.
      Not compatible with `name_pattern`, due to something weird.
    - `order`: Whether to sort tags in ascending or descending order
    - `order_by`: What to sort tags by
- `async def get_tag(self, *, name: Optional[str] = None, tag_id: Optional[int] = None) -> Tag`
    - Get a tag by either name or id
- `async def close(self) -> None`
    - Closes the session

### Post

Attributes
- Represents a Gelbooru post. Should not be constructed manually.
- Check out the docstring for the list of attributes

Methods
- `async def async_download(self, path: Optional[str] = None, *,
  session: Optional[aiohttp.ClientSession] = None,
  stream: Optional[BinaryIO] = None):`
    - Downloads the post asynchronously either to a file, or a stream
    -  You can use a custom aiohttp `session` to download the file

- `def sync_download(self, path: Optional[str] = None, *,
  session: Optional[requests.Session] = None,
  stream: Optional[BinaryIO] = None):`
    - Same as `async_download`, but is synchronous

Magic Methods
- `def __str__(self)`
    - Casting a `Post` to a string returns its `file_url`

### Comment
- Attributes can be found in the docstrings

Magic Methods
- `def __str__(self)`
    - Casting a `Comment` to a string returns `[author]: [content]`

### Tag
- Attributes can be found in the docstrings

- `def __str__(self)`
    - Casting a `Tag` to a string returns the tag name
