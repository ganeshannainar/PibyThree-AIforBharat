import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { cartsAPI, ordersAPI } from '../services/api';
import { useAuth } from './AuthContext';

const CartContext = createContext(null);

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
};

export const CartProvider = ({ children }) => {
  const [cart, setCart] = useState(null);
  const [loading, setLoading] = useState(false);
  const { isAuthenticated } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      fetchCart();
    } else {
      setCart(null);
    }
  }, [isAuthenticated]);

  const fetchCart = useCallback(async () => {
    setLoading(true);
    try {
      const response = await cartsAPI.getAll(1, 100);
      const carts = response.data.data;
      if (carts && carts.length > 0) {
        setCart(carts[carts.length - 1]);
      } else {
        setCart(null);
      }
    } catch (error) {
      console.error('Error fetching cart:', error);
      setCart(null);
    }
    setLoading(false);
  }, []);

  const addToCart = useCallback(async (productId, quantity = 1) => {
    try {
      if (cart) {
        const existingItem = cart.cart_items?.find(item => item.product_id === productId);
        let updatedItems;

        if (existingItem) {
          updatedItems = cart.cart_items.map(item =>
            item.product_id === productId
              ? { product_id: item.product_id, quantity: item.quantity + quantity }
              : { product_id: item.product_id, quantity: item.quantity }
          );
        } else {
          updatedItems = [
            ...cart.cart_items.map(item => ({ product_id: item.product_id, quantity: item.quantity })),
            { product_id: productId, quantity }
          ];
        }

        const response = await cartsAPI.update(cart.id, { cart_items: updatedItems });
        setCart(response.data.data);
      } else {
        const response = await cartsAPI.create({
          cart_items: [{ product_id: productId, quantity }]
        });
        setCart(response.data.data);
      }
      return { success: true };
    } catch (error) {
      console.error('Error adding to cart:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to add to cart'
      };
    }
  }, [cart]);

  const updateCartItem = useCallback(async (productId, quantity) => {
    if (!cart) return { success: false, error: 'No cart found' };

    try {
      let updatedItems;
      if (quantity <= 0) {
        updatedItems = cart.cart_items
          .filter(item => item.product_id !== productId)
          .map(item => ({ product_id: item.product_id, quantity: item.quantity }));
      } else {
        updatedItems = cart.cart_items.map(item =>
          item.product_id === productId
            ? { product_id: item.product_id, quantity }
            : { product_id: item.product_id, quantity: item.quantity }
        );
      }

      if (updatedItems.length === 0) {
        await cartsAPI.delete(cart.id);
        setCart(null);
      } else {
        const response = await cartsAPI.update(cart.id, { cart_items: updatedItems });
        setCart(response.data.data);
      }
      return { success: true };
    } catch (error) {
      console.error('Error updating cart:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to update cart'
      };
    }
  }, [cart]);

  const removeFromCart = useCallback(async (productId) => {
    return updateCartItem(productId, 0);
  }, [updateCartItem]);

  const clearCart = useCallback(async () => {
    if (!cart) return { success: true };

    try {
      await cartsAPI.delete(cart.id);
      setCart(null);
      return { success: true };
    } catch (error) {
      console.error('Error clearing cart:', error);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to clear cart'
      };
    }
  }, [cart]);

  const getCartItemCount = useCallback(() => {
    if (!cart || !cart.cart_items) return 0;
    return cart.cart_items.reduce((total, item) => total + item.quantity, 0);
  }, [cart]);

  const checkout = useCallback(async () => {
    if (!cart) return { success: false, error: 'No cart to checkout' };
    setLoading(true);
    try {
      const response = await ordersAPI.create();
      setCart(null);
      setLoading(false);
      return { success: true, orderId: response.data.id || 'new' };
    } catch (error) {
      console.error('Error during checkout:', error);
      setLoading(false);
      return {
        success: false,
        error: error.response?.data?.detail || 'Failed to place order'
      };
    }
  }, [cart]);

  const value = {
    cart,
    loading,
    addToCart,
    updateCartItem,
    removeFromCart,
    clearCart,
    refreshCart: fetchCart,
    getCartItemCount,
    checkout,
  };

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
};
