import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:local_auth/local_auth.dart';

/// Interface so screens can depend on this rather than the concrete plugin
/// wrapper — lets tests override [biometricAuthProvider] with a fake instead
/// of hitting a real platform channel (which has no responder in the
/// widget-test harness and hangs indefinitely).
abstract class BiometricAuthenticator {
  Future<bool> isAvailable();
  Future<bool> authenticate({String reason});
}

/// Wraps the device's native biometric system (Android Keystore / iOS Secure
/// Enclave). Raw biometric data never leaves the device — only a
/// success/failure boolean crosses into app code (docs/security-model.md).
class BiometricAuth implements BiometricAuthenticator {
  BiometricAuth({LocalAuthentication? auth}) : _auth = auth ?? LocalAuthentication();

  final LocalAuthentication _auth;

  @override
  Future<bool> isAvailable() => _auth.canCheckBiometrics;

  @override
  Future<bool> authenticate({String reason = 'Authenticate to continue'}) {
    return _auth.authenticate(localizedReason: reason);
  }
}

final biometricAuthProvider = Provider<BiometricAuthenticator>((ref) => BiometricAuth());
