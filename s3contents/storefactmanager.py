from s3contents.storefact_fs import StorefactFS
from s3contents.ipycompat import Unicode
from s3contents.genericmanager import GenericContentsManager


class StorefactContentsManager(GenericContentsManager):
    store_url = Unicode(
        "store_url", help="Storefact URL which configures the notebook store").tag(
            config=True, env="JPYNB_STOREFACT_URL")

    prefix = Unicode("", help="Prefix path inside the specified bucket").tag(config=True)
    separator = Unicode("/", help="Path separator").tag(config=True)

    def __init__(self, *args, **kwargs):
        super(StorefactContentsManager, self).__init__(*args, **kwargs)

        self._fs = StorefactFS(
            log=self.log,
            store_url=self.store_url,
            prefix=self.prefix,
            separator=self.separator)
