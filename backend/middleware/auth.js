const jwt = require('jsonwebtoken');

const authenticateToken = (req, res, next) => {
  const authHeader = req.headers['authorization'];

  if (!authHeader) {
    return res.status(401).json({
      success: false,
      error: 'Access denied. No authorization header provided.',
    });
  }

  const parts = authHeader.split(' ');
  if (parts.length !== 2 || parts[0] !== 'Bearer') {
    return res.status(401).json({
      success: false,
      error: 'Invalid authorization format. Use: Bearer <token>',
    });
  }

  const token = parts[1];

  if (!token) {
    return res.status(401).json({
      success: false,
      error: 'Access denied. Token missing.',
    });
  }

  try {
    const secret = process.env.JWT_SECRET || 'change_me_in_env';
    const decoded = jwt.verify(token, secret);
    req.user = decoded;
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        error: 'Token expired. Please log in again.',
      });
    }
    return res.status(403).json({
      success: false,
      error: 'Invalid token.',
    });
  }
};

module.exports = { authenticateToken };
