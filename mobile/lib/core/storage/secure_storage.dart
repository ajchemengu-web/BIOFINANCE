import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Interface so the auth layer can depend on this rather than the concrete
/// plugin wrapper — lets tests override [secureStorageProvider] with an
/// in-memory fake instead of hitting a real platform channel.
abstract class TokenStorage {
  Future<void> write(String key, String value);
  Future<String?> read(String key);
  Future<void> delete(String key);
}

/// Encrypted local storage for session tokens. Never used for raw biometric
/// data or Daraja credentials — those never reach the client at all.
class SecureStorage implements TokenStorage {
  SecureStorage({FlutterSecureStorage? storage})
      : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;

  @override
  Future<void> write(String key, String value) => _storage.write(key: key, value: value);

  @override
  Future<String?> read(String key) => _storage.read(key: key);

  @override
  Future<void> delete(String key) => _storage.delete(key: key);
}

final secureStorageProvider = Provider<TokenStorage>((ref) => SecureStorage());
