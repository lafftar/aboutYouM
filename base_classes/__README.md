# base class structure.

## base
- This class imports all the abstracts, adds a `.run()` flow, and provides them to top level classes like
`restock_monitor` and `new_product_monitor`. 
  - _(Which in turn get used by `main`, `api` and `dbot` runners.)_

## req:
```http request
GET /v1/filters HTTP/1.1
Host: api-cloud.aboutyou.de
If-None-Match:
```

- Trying to find which backend this is?
  - https://developers.pipedrive.com/docs/api/v1/Filters
  - different look, but similar mindset maybe.