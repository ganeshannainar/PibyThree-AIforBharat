import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { productsAPI } from '../services/api';
import ProductCard from '../components/ProductCard';

const Products = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [searchInput, setSearchInput] = useState(searchParams.get('search') || '');
  const limit = 12;

  // Read search from URL on mount and when URL changes
  useEffect(() => {
    const urlSearch = searchParams.get('search') || '';
    if (urlSearch !== search) {
      setSearch(urlSearch);
      setSearchInput(urlSearch);
      setPage(1);
    }
  }, [searchParams]);

  useEffect(() => {
    fetchProducts();
  }, [page, search]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await productsAPI.getAll(page, limit, search);
      setProducts(response.data.data || []);
    } catch (error) {
      console.error('Error fetching products:', error);
      setProducts([]);
    }
    setLoading(false);
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    setSearch(searchInput.toLowerCase());
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setSearch('');
    setPage(1);
  };

  return (
    <div className="products-page">
      <div className="products-header">
        <h1>All Products</h1>
        <form onSubmit={handleSearch} className="search-box">
          <input
            type="text"
            placeholder="Search products..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button type="submit" className="btn btn-primary">Search</button>
          {search && (
            <button type="button" onClick={handleClearSearch} className="btn btn-secondary">
              Clear
            </button>
          )}
        </form>
      </div>

      {search && (
        <p style={{ marginBottom: '20px', color: '#7f8c8d' }}>
          Showing results for: "{search}"
        </p>
      )}

      {loading ? (
        <div className="loading">Loading products...</div>
      ) : products.length > 0 ? (
        <>
          <div className="products-grid">
            {products.map(product => (
              <ProductCard key={product.id} product={product} />
            ))}
          </div>
          
          <div className="pagination">
            <button 
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
            >
              Previous
            </button>
            <button className="active">{page}</button>
            <button 
              onClick={() => setPage(p => p + 1)}
              disabled={products.length < limit}
            >
              Next
            </button>
          </div>
        </>
      ) : (
        <div className="loading">
          {search ? 'No products found matching your search.' : 'No products available.'}
        </div>
      )}
    </div>
  );
};

export default Products;
