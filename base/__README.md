# base class structure.

## base
- This class imports all the abstracts, adds a `.run()` flow, and provides them to top level classes like
`restock_monitor` and `new_product_monitor`. 
  - _(Which in turn get used by `main`, `api` and `dbot` runners.)_