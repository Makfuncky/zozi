export const getWishlistButtonText = (inWishlist: boolean): string =>
  inWishlist ? "Remove from wishlist" : "Add to wishlist";

export const getWishlistIcon = (inWishlist: boolean): string =>
  inWishlist ? "❤️" : "🤍";
