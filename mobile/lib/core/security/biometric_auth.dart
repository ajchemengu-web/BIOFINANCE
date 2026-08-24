import 'package:local_auth/local_auth.dart';

/// Wraps the device's native biometric system (Android Keystore / iOS Secure
/// Enclave). Raw biometric data never leaves the device — only a
/// success/failure boolean crosses into app code (docs/security-model.md).
class BiometricAuth {
  BiometricAuth({LocalAuthentication? auth}) : _auth = auth ?? LocalAuthentication();

  final LocalAuthentication _auth;

  Future<bool> isAvailable() => _auth.canCheckBiometrics;

  Future<bool> authenticate({String reason = 'Authenticate to continue'}) {
    return _auth.authenticate(localizedReason: reason);
  }
}
