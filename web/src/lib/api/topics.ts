import { apiFetch } from "@/lib/api";
import type { TopicV3, TopicDetailV3 } from "@/components/topics/types";

export const topicsApi = {
  getV3: (subject: string): Promise<TopicV3[]> =>
    apiFetch<TopicV3[]>(`/topics/v3?subject=${encodeURIComponent(subject)}`),

  getTopicDetail: (topicId: string, subject: string): Promise<TopicDetailV3> =>
    apiFetch<TopicDetailV3>(
      `/topics/v3/${encodeURIComponent(topicId)}?subject=${encodeURIComponent(subject)}`
    ),
};
