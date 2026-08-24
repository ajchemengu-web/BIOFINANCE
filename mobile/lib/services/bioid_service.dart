import 'dart:math';

const _alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';

/// Mirrors backend/app/services/bioid_service.py generate_bio_id_code — used
/// for mock/local Phase 1 UI only. Real issuance is server-side (Phase 2).
String generateBioIdCode() {
  final random = Random();
  final suffix = List.generate(6, (_) => _alphabet[random.nextInt(_alphabet.length)]).join();
  return 'BF-$suffix';
}
