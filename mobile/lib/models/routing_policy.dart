enum RoutingMode { primary, priority, automatic, manual }

RoutingMode _modeFromString(String value) =>
    RoutingMode.values.firstWhere((m) => m.name.toUpperCase() == value, orElse: () => RoutingMode.primary);

/// Mirrors backend/app/schemas/routing.py. `primaryProviderId`/
/// `fallbackProviderId` are ProviderConnection UUIDs, not provider codes.
class RoutingPolicy {
  const RoutingPolicy({required this.mode, this.primaryProviderId, this.fallbackProviderId});

  final RoutingMode mode;
  final String? primaryProviderId;
  final String? fallbackProviderId;

  factory RoutingPolicy.fromJson(Map<String, dynamic> json) => RoutingPolicy(
        mode: _modeFromString(json['mode'] as String),
        primaryProviderId: json['primary_provider_id'] as String?,
        fallbackProviderId: json['fallback_provider_id'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'mode': mode.name.toUpperCase(),
        'primary_provider_id': primaryProviderId,
        'fallback_provider_id': fallbackProviderId,
      };
}
