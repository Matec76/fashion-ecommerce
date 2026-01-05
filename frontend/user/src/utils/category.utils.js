import { API_ENDPOINTS } from '../config/api.config';
import logger from './logger';

/**
 * Get all category IDs including children (hierarchical)
 * @param {number} parentCategoryId - Parent category ID
 * @returns {Promise<number[]>} Array of category IDs (parent + children)
 */
export const getCategoryWithChildren = async (parentCategoryId) => {
    try {
        const response = await fetch(API_ENDPOINTS.CATEGORIES.DETAIL(parentCategoryId));

        if (!response.ok) {
            logger.error(`Failed to fetch category ${parentCategoryId}`);
            return [parentCategoryId];
        }

        const categoryData = await response.json();

        // Collect all IDs (parent + children)
        const categoryIds = [parentCategoryId];

        if (categoryData.children && categoryData.children.length > 0) {
            categoryData.children.forEach(child => {
                categoryIds.push(child.category_id);

                // Recursive: if child has children (nested categories)
                if (child.children && child.children.length > 0) {
                    child.children.forEach(grandChild => {
                        categoryIds.push(grandChild.category_id);
                    });
                }
            });
        }

        logger.log(`Category ${parentCategoryId} hierarchy:`, categoryIds);
        return categoryIds;

    } catch (error) {
        logger.error(`Error fetching category hierarchy for ${parentCategoryId}:`, error);
        return [parentCategoryId];
    }
};

/**
 * Fetch featured products from multiple categories
 * @param {number[]} categoryIds - Array of category IDs
 * @param {number} limit - Max products per category
 * @returns {Promise<Array>} Array of featured products
 */
export const getFeaturedProductsFromCategories = async (categoryIds, limit = 50) => {
    try {
        // Fetch from all categories in parallel
        const promises = categoryIds.map(id =>
            fetch(`${API_ENDPOINTS.PRODUCTS.FEATURED}?category_id=${id}&limit=${limit}`)
                .then(res => res.ok ? res.json() : [])
                .catch(() => [])
        );

        const productsArrays = await Promise.all(promises);
        const allProducts = productsArrays.flat();

        // Deduplicate by product_id
        const uniqueProducts = Array.from(
            new Map(allProducts.map(p => [p.product_id || p.id, p])).values()
        );

        logger.log(`Found ${uniqueProducts.length} unique featured products from ${categoryIds.length} categories`);
        return uniqueProducts;

    } catch (error) {
        logger.error('Error fetching featured products:', error);
        return [];
    }
};

/**
 * Get featured products for a parent category (including all children)
 * @param {number} parentCategoryId - Parent category ID  
 * @param {number} limit - Max products per category
 * @returns {Promise<Array>} Array of featured products
 */
export const getFeaturedWithHierarchy = async (parentCategoryId, limit = 50) => {
    const categoryIds = await getCategoryWithChildren(parentCategoryId);
    return await getFeaturedProductsFromCategories(categoryIds, limit);
};
