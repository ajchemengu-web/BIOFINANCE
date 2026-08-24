import '../core/networking/api_client.dart';
import '../models/bio_id.dart';

/// Talks to GET/POST /bioid. Implemented once the backend leaves stub state
/// (Phase 2, docs/roadmap.md).
class BioIdRepository {
  BioIdRepository({ApiClient? apiClient}) : _apiClient = apiClient ?? ApiClient();

  // ignore: unused_field
  final ApiClient _apiClient;

  Future<BioId> fetchCurrent() {
    throw UnimplementedError('BioIdRepository.fetchCurrent — implemented in Phase 2');
  }
}
