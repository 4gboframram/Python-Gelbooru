import asyncio
import datetime
import typing

import aiohttp
import xmltodict

from python_gelbooru.classes import Post, Comment, Tag, ImageDimensions
from python_gelbooru.exceptions import GelbooruLimitError


class AsyncGelbooru:
    """
    The class used to search Gelbooru asynchronously.
    """

    BASE_API_URL: typing.ClassVar[str] = 'https://gelbooru.com/index.php?page=dapi&q=index&json=1'
    POSTS_HARD_LIMIT: typing.ClassVar[int] = 1000

    def __init__(self, *, api_key: typing.Optional[str] = None, user_id: typing.Optional[str] = None):
        self.session = aiohttp.ClientSession()
        if (api_key or user_id) and not (api_key and user_id):
            raise ValueError("Both api key and user id must be specified if specified")

        self.url = AsyncGelbooru.BASE_API_URL + f"&api_key={api_key}&user_id={user_id}" if (
                api_key and user_id) else AsyncGelbooru.BASE_API_URL

    @staticmethod
    def _format_tags(include_tags: typing.Iterable[str], exclude_tags: typing.Iterable[str] = None) -> str:
        include = '+'.join(tag.strip().lower().replace(' ', '_') for tag in include_tags)
        exclude = '+'.join('-' + tag.strip().lstrip('-').lower().replace(' ', '_') for tag in
                           exclude_tags) if exclude_tags else ''
        return include + '+' + exclude

    async def search_posts(self,
                           tags: typing.Iterable[str],
                           *, exclude_tags: typing.Iterable[str] = None,
                           limit=1, page_number: int = 0, random: bool = False
                           ) -> typing.Tuple[Post, ...]:
        """
        Searches Gelbooru with the given include and exclude tags. Grabs page 0 by default

        :param tags: The include tags
        :param exclude_tags: The exclude tags
        :param limit: The (maximum) number of posts to grab
        :param page_number: The page number (with respect to the limit) of search results to find
        :param random: Whether to return random posts with the tags.
        :raises: GelbooruLimitError
        :return: A tuple of returned posts
        :raises: GelbooruLimitError: Limit > 1000
        """
        if limit > 1000:
            raise GelbooruLimitError("Gelbooru can only return 1000 items in a single request")

        if random:
            tags = list(tags) + ['sort:random']

        url = self.url + '&tags=' + self._format_tags(tags, exclude_tags) + f'&limit={limit}&s=post'

        if page_number:
            url += f'&pid={page_number}'
        async with self.session.get(url) as response:
            json = await response.json()

        print(url)
        return tuple(Post(data=post, source=post['source'], file_url=post['file_url'], width=post['width'],
                          height=post['height'],
                          id=post['id'], owner=post['owner'], rating=post['rating'], score=post['score'],
                          parent_id=post['parent_id'], tags=post['tags'].split(), title=post['title'],
                          created_at=post['created_at'], md5=post['hash'], locked=bool(post['post_locked']),
                          file_name=post['image']
                          ) for post in json)

    async def get_post(self, *, post_id: typing.Optional[int] = None,
                       md5: typing.Optional[str] = None) -> typing.Tuple[Post, ...]:
        """
        Get a post either by id or by md5 hash
        :param post_id: The id of the post to get
        :param md5: The md5 hash of the post
        :return: A tuple (almost always of a single element) that contains the post / matching posts.
        :raises ValueError: If there is not a post id or an md5 hash, or there is both
        """
        if (post_id and md5) or (not post_id and not md5):
            raise ValueError("Must specify a post id or an md5, and not both.")

        if md5:
            url = self.url + f'&tags=md5:{md5}'

        else:
            url = self.url + f'&id={post_id}'
        url += '&s=post'

        async with self.session.get(url) as response:
            json = await response.json()

        res = tuple([Post(data=post, source=post['source'], file_url=post['file_url'], width=post['width'],
                          height=post['height'], id=post['id'], owner=post['owner'], rating=post['rating'],
                          score=post['score'], parent_id=post['parent_id'], tags=post['tags'].split(),
                          title=post['title'], created_at=post['created_at'],
                          md5=post['hash'], locked=bool(post['post_locked']),
                          file_name=post['image']
                          ) for post in json])
        if md5:
            if res[0].md5 != md5:
                return ()
            return res
        return res

    async def get_post_comments(self, post: Post) -> typing.Tuple[Comment, ...]:
        url = f"{self.url.replace('&json=1', '')}&s=comment&post_id={post.id}"
        async with self.session.get(url) as response:
            xml = await response.text()
            parsed = xmltodict.parse(xml)['comments'].get('comment')
            # print(parsed)
        if parsed:
            return tuple(Comment(
                data=comment,
                created_at=datetime.datetime.strptime(comment['@created_at'], "%Y-%m-%d %H:%M"),
                post_id=int(comment['@post_id']),
                content=comment['@body'],
                author=comment['@creator'],
                comment_id=int(comment['@id']),
                author_id=int(comment['@creator_id'])
            ) for comment in parsed)
        else:
            return ()

    async def search_tags(self, names: typing.Optional[typing.Iterable[str]] = None, limit: int = 1, *,
                          name_pattern: typing.Optional[str] = None,
                          after_id: typing.Optional[int] = None,
                          order: typing.Optional[typing.Literal['asc', 'desc']] = None,
                          order_by: typing.Optional[typing.Literal['date', 'count', 'name']] = None) -> typing.Tuple[Tag, ...]:
        """
        Search for Gelbooru tags

        :param names: A list of names to get the tag info from.
        :param limit: The maximum amount of tags to grab.
        :param name_pattern: A wildcard-based search for searching for tags. '_' represents a single character wildcard,
         and '%' represents a multi-character wildcard.
        :param after_id: Return tags with an id greater than this id.
        :param order: Either ascending ('asc') or descending ('desc'), the order in which to return tags.
        :param order_by: Order by a field: ('date', 'count', 'name')
        :return: A tuple of tags that match the criteria.
        :raises: ValueError: Bad parameters
        """
        url = self.url + "&s=tag"
        if names and name_pattern:
            raise ValueError("Must have one of names and name pattern")

        if name_pattern and after_id:
            raise ValueError("For some odd reason, name patterns and after id's don't work together")

        if names:
            url += f"&names={self._format_tags(names)}"

        if name_pattern:
            url += f"&name_pattern={name_pattern}"

        if after_id is not None:
            url += f"&after_id={after_id}"

        if order_by:
            if order_by not in ('date', 'count', 'name'):
                raise ValueError("If ordering of tags specified, it must be either 'date', 'count', or 'name'")

            url += f"&orderby={order_by}"

        if order:
            if order.lower() not in ('asc', 'desc'):
                raise ValueError(f"Order can only be 'asc' or 'desc'. '{order}' was received.")
            url += f"&{order=!s}"

        url += f"&{limit=}"
        print(url)
        async with self.session.get(url) as response:
            json = await response.json()

        return tuple([Tag(id=int(tag['id']), name=tag['tag'], type=tag['type'],
                          count=int(tag['count']), ambiguous=bool(int(tag['ambiguous'])),
                          ) for tag in json])

    async def get_tag(self, *, name: typing.Optional[str] = None, tag_id: typing.Optional[int] = None) -> Tag:

        if name and tag_id or (not name and not tag_id):
            raise ValueError("Must specify a name or tag id, and not both")

        url = self.url + '&s=tag'

        if name:
            url += f'&name={self._format_tags([name]).rstrip("+")}'
        else:
            url += f'&id={tag_id}'

        async with self.session.get(url) as response:
            json = (await response.json())[0]
            return Tag(id=int(json['id']), name=json['tag'], type=json['type'],
                       count=int(json['count']), ambiguous=bool(int(json['ambiguous'])))

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    async def close(self):
        await self.session.close()


async def main():
    async with AsyncGelbooru(api_key='4b34a0cf4d4f367d58c6a8dd8fa0b64387c1c16358481ab677e41639b6e4462e',
                             user_id='839992') as gel:
        yuyu = await gel.search_posts(['saigyouji yuyuko', 'webm', 'rating:explicit'], limit=100, random=True)
        p = await gel.get_post(post_id=3633777)
        comments = await gel.get_post_comments(p[0])
        print([str(i) for i in comments])

        tasks = [i.async_download(f"./arts/{i.id}") for i in yuyu]
        await asyncio.gather(*tasks)


async def main2():
    async with AsyncGelbooru(api_key='4b34a0cf4d4f367d58c6a8dd8fa0b64387c1c16358481ab677e41639b6e4462e',
                             user_id='839992') as gel:
        tag = await gel.get_tag(tag_id=262)
        print(tag)
        print(tag.__repr__())


async def main3():
    async with AsyncGelbooru(api_key='4b34a0cf4d4f367d58c6a8dd8fa0b64387c1c16358481ab677e41639b6e4462e',
                             user_id='839992') as gel:
        p = await gel.search_tags(name_pattern="%yuyu%", limit=10, order_by='count', order='desc')
        [print(i, i.id, i.count) for i in p]

        print(p)
        # [print(i) for i in p]

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
