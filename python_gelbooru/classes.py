import datetime
import os.path
import typing
from collections import namedtuple
from dataclasses import dataclass, field

import aiohttp
import requests

ImageDimensions = namedtuple('ImageDimensions', ['width', 'height'])


@dataclass(init=True, frozen=True)
class Post:
    """
    An object that represents a Gelbooru post. It contains most useful information about the post.
    If you want more advanced data, access the data member of the class

    Attributes
        data: dict - The dictionary that contains the full data of the post

        source: str - The url for the source of the image

        file_url: str - The url for file of the post

        width: int - The width of the artwork

        height: int - The height of the artwork

        id: int - The id of the post

        owner: str - The name of the site that owns the artwork.

        rating: str - The "safeness" rating of the post. Not to be confused with score

        score: int - The score of the post. Not to be confused with rating

        parent_id: Union[str, int] - The id of the parent post

        tags: List[str, ...] - The list of tags the post has

        title: str - The title of the post,

        created_at: str - A string that represents the time the artwork was posted

        md5: str - The md5 hash of the post

        locked: bool - Whether the post is locked

        file_name: str - The name of the file of the post

    Properties:
        dimensions: ImageDimensions - A NamedTuple that contains the art dimensions data (the width and height)

        extension: the file extension of the artwork

    Methods:
        async def async_download - Downloads a post asynchronously

        def sync_download - Downloads a post synchronously

    """
    data: dict
    source: str
    file_url: str
    width: int
    height: int

    id: int
    owner: str
    rating: str
    score: int
    parent_id: typing.Union[str, int]
    tags: typing.List[str]
    title: str
    created_at: str
    md5: str
    locked: bool
    file_name: str

    @property
    def extension(self):
        return os.path.splitext(self.file_name)[1]

    @property
    def dimensions(self) -> ImageDimensions:
        return ImageDimensions(self.width, self.height)

    async def async_download(self, path: typing.Optional[str] = None, *,
                             session: typing.Optional[aiohttp.ClientSession] = None,
                             stream: typing.Optional[typing.BinaryIO] = None):
        """
        Downloads the file of the post to the path provided with aiohttp
        :param path:  The file path to write to. If not given, defaults to self.file_name.
        If a file extension is not in the name of the file, it is added automatically
        :param session: An Aiohttp client session that will be used to download the post.
        :param stream: The BinaryIO stream to write the image to. Not compatible with path.
        :return: None
        """
        if path and stream:
            raise ValueError("Only one of path and stream may be provided")

        if session:
            async with session.get(self.file_url) as response:
                binary = await response.read()
        else:
            async with aiohttp.ClientSession() as sess:
                async with sess.get(self.file_url) as response:
                    binary = await response.read()

        if not path and not stream:
            path = self.file_name

        elif path:
            if not os.path.splitext(path)[1]:
                path += self.extension
            with open(path, 'wb+') as f:
                f.write(binary)
        else:
            stream.write(binary)

    def sync_download(self, path: typing.Optional[str] = None, *,
                      session: typing.Optional[requests.Session] = None,
                      stream: typing.Optional[typing.BinaryIO] = None):
        """
        Downloads the file of the post to the path provided
        :param path: The file path to write to. If not given, defaults to self.file_name.
        If a file extension is not in the name of the file, it is added automatically. Not compatible with stream
        :param session: The requests.Session object to use to get the data
        :param stream: The BinaryIO stream to write the image to. Not compatible with path.
        :return:
        """
        if path and stream:
            raise ValueError("Only one of path and stream may be provided")

        if not path and not stream:
            path = self.file_name
        elif path:
            if not os.path.splitext(path)[1]:
                path += self.extension

        if session:
            response = session.get(self.file_url)

        else:
            response = requests.get(self.file_url)

        if stream:
            stream.write(response.content)
        else:
            with open(path, 'wb+') as f:
                f.write(response.content)

    def __str__(self):
        return self.file_url


@dataclass(init=True, frozen=True)
class Comment:
    """
    A class that represents a Gelbooru comment

    Attributes
        data: dict - The dictionary that contains the original comment data

        created_at: datetime.datetime - The time the comment was created at.

        post_id: int - The id of the post that the comment is on

        content: str - The content of the comment

        author: str - The name of the user that posted the comment. Oftentimes "Anonymous".

        comment_id: int - The id of the comment itself.

        author_id: int - The id of the user that posted the comment

    Magic Methods:
        str(self) -> f"{self.author}: {self.content}"
    """
    data: dict
    created_at: datetime.datetime
    post_id: int
    content: str
    author: str
    comment_id: int
    author_id: int

    def __str__(self):
        return f"{self.author}: {self.content}"


@dataclass(frozen=True, init=True)
class Tag:
    """
    A class that represents a Gelbooru tag.

    Attributes
        id: int - The id of the tag. Often used for getting the tag.

        type: str - The type of tag it is. Example values are 'copyright', 'metadata', and 'tag.'

        name: str - The name of the tag. This has the underscores in it and should always be lowercase.

        count: int - The number of posts that have this tag.

        ambiguous: bool - Whether the tag is ambiguous.

    Properties:
        is_meta: bool - Whether tag is a metadata tag. Useful for some uses.

    Magic Methods:
        str(self) -> self.name

    """
    id: int = field(hash=True, compare=True)  # Don't ask me why. My friend told me to
    type: str

    name: str
    count: int

    ambiguous: bool

    @property
    def is_meta(self) -> bool:
        return self.type == "metadata"

    def __str__(self):
        return self.name
