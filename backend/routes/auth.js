const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { pool } = require('../db/index');
const { authenticateToken } = require('../middleware/auth');

const router = express.Router();

const generateToken = (user) => {
  const secret = process.env.JWT_SECRET || 'change_me_in_env';
  return jwt.sign(
    {
      id: user.id,
      email: user.email,
      name: user.name,
      surname: user.surname,
    },
    secret,
    { expiresIn: '7d' }
  );
};

const validateEmail = (email) => {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(String(email).toLowerCase());
};

// POST /api/auth/register
router.post('/register', async (req, res) => {
  try {
    const { name, surname, email, password } = req.body;

    // Validation
    if (!name || !surname || !email || !password) {
      return res.status(400).json({
        success: false,
        error: 'All fields are required: name, surname, email, password.',
      });
    }

    if (name.trim().length < 2) {
      return res.status(400).json({
        success: false,
        error: 'Name must be at least 2 characters long.',
      });
    }

    if (surname.trim().length < 2) {
      return res.status(400).json({
        success: false,
        error: 'Surname must be at least 2 characters long.',
      });
    }

    if (!validateEmail(email)) {
      return res.status(400).json({
        success: false,
        error: 'Please provide a valid email address.',
      });
    }

    if (password.length < 8) {
      return res.status(400).json({
        success: false,
        error: 'Password must be at least 8 characters long.',
      });
    }

    // Check if user already exists
    const existingUser = await pool.query(
      'SELECT id FROM users WHERE email = $1',
      [email.toLowerCase().trim()]
    );

    if (existingUser.rows.length > 0) {
      return res.status(409).json({
        success: false,
        error: 'An account with this email already exists.',
      });
    }

    // Hash password
    const saltRounds = 12;
    const password_hash = await bcrypt.hash(password, saltRounds);

    // Insert user
    const result = await pool.query(
      `INSERT INTO users (name, surname, email, password_hash)
       VALUES ($1, $2, $3, $4)
       RETURNING id, name, surname, email, created_at`,
      [name.trim(), surname.trim(), email.toLowerCase().trim(), password_hash]
    );

    const newUser = result.rows[0];
    const token = generateToken(newUser);

    return res.status(201).json({
      success: true,
      message: 'Account created successfully. Welcome aboard, Commander!',
      token,
      user: {
        id: newUser.id,
        name: newUser.name,
        surname: newUser.surname,
        email: newUser.email,
        avatar: null,
        createdAt: newUser.created_at,
      },
    });
  } catch (err) {
    console.error('[AUTH] Register error:', err.message);
    return res.status(500).json({
      success: false,
      error: 'Internal server error. Please try again later.',
    });
  }
});

// POST /api/auth/login
router.post('/login', async (req, res) => {
  try {
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({
        success: false,
        error: 'Email and password are required.',
      });
    }

    if (!validateEmail(email)) {
      return res.status(400).json({
        success: false,
        error: 'Please provide a valid email address.',
      });
    }

    // Find user
    const result = await pool.query(
      'SELECT id, name, surname, email, password_hash, avatar FROM users WHERE email = $1',
      [email.toLowerCase().trim()]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({
        success: false,
        error: 'Invalid email or password.',
      });
    }

    const user = result.rows[0];

    // Verify password
    const isMatch = await bcrypt.compare(password, user.password_hash);

    if (!isMatch) {
      return res.status(401).json({
        success: false,
        error: 'Invalid email or password.',
      });
    }

    const token = generateToken(user);

    return res.status(200).json({
      success: true,
      message: `Welcome back, Commander ${user.name}!`,
      token,
      user: {
        id: user.id,
        name: user.name,
        surname: user.surname,
        email: user.email,
        avatar: user.avatar || null,
      },
    });
  } catch (err) {
    console.error('[AUTH] Login error:', err.message);
    return res.status(500).json({
      success: false,
      error: 'Internal server error. Please try again later.',
    });
  }
});

// PUT /api/auth/profile
router.put('/profile', authenticateToken, async (req, res) => {
  try {
    const { name, surname } = req.body;
    const userId = req.user.id;

    if (!name || !surname) {
      return res.status(400).json({ success: false, error: 'Name and surname are required.' });
    }
    if (name.trim().length < 2 || surname.trim().length < 2) {
      return res.status(400).json({ success: false, error: 'Name and surname must be at least 2 characters.' });
    }

    const result = await pool.query(
      `UPDATE users SET name = $1, surname = $2 WHERE id = $3
       RETURNING id, name, surname, email, avatar`,
      [name.trim(), surname.trim(), userId]
    );

    const updated = result.rows[0];
    const secret = process.env.JWT_SECRET || 'change_me_in_env';
    const token = jwt.sign(
      { id: updated.id, email: updated.email, name: updated.name, surname: updated.surname },
      secret,
      { expiresIn: '7d' }
    );

    return res.status(200).json({
      success: true,
      message: 'Profile updated successfully.',
      token,
      user: { id: updated.id, name: updated.name, surname: updated.surname, email: updated.email, avatar: updated.avatar || null },
    });
  } catch (err) {
    console.error('[AUTH] Profile update error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

// PUT /api/auth/password
router.put('/password', authenticateToken, async (req, res) => {
  try {
    const { currentPassword, newPassword } = req.body;
    const userId = req.user.id;

    if (!currentPassword || !newPassword) {
      return res.status(400).json({ success: false, error: 'Current and new password are required.' });
    }
    if (newPassword.length < 8) {
      return res.status(400).json({ success: false, error: 'New password must be at least 8 characters.' });
    }

    const result = await pool.query('SELECT password_hash FROM users WHERE id = $1', [userId]);
    const user = result.rows[0];

    const isMatch = await bcrypt.compare(currentPassword, user.password_hash);
    if (!isMatch) {
      return res.status(401).json({ success: false, error: 'Current password is incorrect.' });
    }

    const newHash = await bcrypt.hash(newPassword, 12);
    await pool.query('UPDATE users SET password_hash = $1 WHERE id = $2', [newHash, userId]);

    return res.status(200).json({ success: true, message: 'Password changed successfully.' });
  } catch (err) {
    console.error('[AUTH] Password change error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

// PUT /api/auth/avatar — set or remove user's profile photo
// Body: { avatar: "data:image/jpeg;base64,..." }   to set
//       { avatar: null }                            to remove
router.put('/avatar', authenticateToken, async (req, res) => {
  try {
    const { avatar } = req.body;
    const userId = req.user.id;

    // null/empty → clear
    if (avatar === null || avatar === '' || typeof avatar === 'undefined') {
      await pool.query('UPDATE users SET avatar = NULL WHERE id = $1', [userId]);
      return res.status(200).json({ success: true, avatar: null });
    }

    if (typeof avatar !== 'string' || !avatar.startsWith('data:image/')) {
      return res.status(400).json({ success: false, error: 'Avatar must be a data:image/* URL.' });
    }
    // Cap at ~3MB base64 (≈2.2MB binary) to keep DB row reasonable
    if (avatar.length > 3 * 1024 * 1024) {
      return res.status(413).json({ success: false, error: 'Avatar too large. Try a smaller crop or a more compressed JPEG.' });
    }

    await pool.query('UPDATE users SET avatar = $1 WHERE id = $2', [avatar, userId]);
    return res.status(200).json({ success: true, avatar });
  } catch (err) {
    console.error('[AUTH] Avatar update error:', err.message);
    return res.status(500).json({ success: false, error: 'Internal server error.' });
  }
});

module.exports = router;
